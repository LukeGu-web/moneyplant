from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Book
from .serializers import BookSerializer


@api_view(http_method_names=["POST"])
@permission_classes([IsAuthenticated])
def create_book_with_groups(request):
    if request.method == "POST":
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            # Set the user before saving
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookList(generics.ListCreateAPIView):
    """
    List all Books, or create a new Book.
    """
    queryset = Book.objects.get_queryset()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        books = Book.objects.filter(user=self.request.user)
        return books

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a Book instance.
    """
    queryset = Book.objects.get_queryset()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]
    # permission_classes = [IsOwner]

    def get_queryset(self):
        books = Book.objects.filter(user=self.request.user)
        return books
