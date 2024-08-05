from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from .models import Book
from .serializers import BookSerializer


class BookList(generics.ListCreateAPIView):
    """
    List all Books, or create a new Book.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        books = Book.objects.filter(user=self.request.user)
        return books
    queryset = Book.objects.get_queryset()
    serializer_class = BookSerializer


class BookDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a Book instance.
    """
    permission_classes = [IsAuthenticated]
    # permission_classes = [IsOwner]

    def get_queryset(self):
        books = Book.objects.filter(user=self.request.user)
        return books
    queryset = Book.objects.get_queryset()
    serializer_class = BookSerializer
