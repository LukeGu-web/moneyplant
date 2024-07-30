from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
# from rest_framework.authtoken.models import Token
from .models import Book
from .serializers import BookSerializer
# from .permissions import IsOwnerOrReadonly, IsOwner


class BookList(APIView):
    """
    List all Books, or create a new Book.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        books = Book.objects.filter(user=request.user)
        serializer = BookSerializer(books, many=True)
        if books.exists():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No book found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, format=None):
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookDetail(APIView):
    """
    Retrieve, update or delete a Book instance.
    """
    # permission_classes = [IsOwner]

    def get_object(self, pk):
        try:
            return Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        book = self.get_object(pk)
        if book.user == request.user:
            serializer = BookSerializer(book)
            return Response(serializer.data)
        else:
            return Response({'error': 'No book found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk, format=None):
        book = self.get_object(pk)
        if book.user != request.user:
            return Response({'error': 'Wrong credential'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = BookSerializer(book, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        book = self.get_object(pk)
        if book.user != request.user:
            return Response({'error': 'Wrong credential'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            book.delete()
            return Response({'message': 'Delete successfully'}, status=status.HTTP_204_NO_CONTENT)
