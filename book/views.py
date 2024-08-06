from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Book
from .serializers import BookSerializer


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
