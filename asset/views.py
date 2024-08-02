from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from book.models import Book
from .models import Asset, AssetGroup
from .serializers import AssetSerializer, AssetGroupSerializer
# from .permissions import IsOwnerOrReadonly, IsOwner


class AssetGroupList(generics.ListCreateAPIView):
    """
    List all Asset groups, or create a new Asset group.
    """
    permission_classes = [IsAuthenticated]

    queryset = AssetGroup.objects.all()
    serializer_class = AssetGroupSerializer


class AssetGroupDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an AssetGroup instance.
    """
    permission_classes = [IsAuthenticated]

    queryset = AssetGroup.objects.all()
    serializer_class = AssetGroupSerializer


class AssetList(generics.ListCreateAPIView):
    """
    List all Assets, or create a new Asset.
    """
    permission_classes = [IsAuthenticated]

    queryset = Asset.objects.all()
    serializer_class = AssetSerializer


class AssetDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an Asset instance.
    """
    permission_classes = [IsAuthenticated]

    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
