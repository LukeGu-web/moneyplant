from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from book.models import Book
from .models import Asset
from .serializers import AssetSerializer
# from .permissions import IsOwnerOrReadonly, IsOwner


class AssetList(APIView):
    """
    List all Assets, or create a new Asset.
    """
    # permission_classes = [IsAuthenticated]


class AssetDetail(APIView):
    """
    Retrieve, update or delete a Asset instance.
    """
    # permission_classes = [IsOwner]
