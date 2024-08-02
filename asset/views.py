from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from book.models import Book
from .models import Asset, AssetGroup
from .serializers import AssetSerializer, AssetGroupSerializer
# from .permissions import IsOwnerOrReadonly, IsOwner


class AssetGroupList(APIView):
    """
    List all Assets, or create a new Asset.
    """

    def get(self, request):
        all_groups = AssetGroup.objects.all()
        serializer = AssetGroupSerializer(all_groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AssetList(APIView):
    """
    List all Assets, or create a new Asset.
    """
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        assets = Asset.objects.all()
        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# class AssetDetail(APIView):
#     """
#     Retrieve, update or delete a Asset instance.
#     """
#     # permission_classes = [IsOwner]
