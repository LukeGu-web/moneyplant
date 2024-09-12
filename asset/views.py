from django.db.models import Sum, Case, When, F, DecimalField
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from book.models import Book
from .models import Asset, AssetGroup
from .serializers import AssetSerializer, AssetGroupSerializer


class AssetGroupList(generics.ListCreateAPIView):
    """
    List all Asset groups, or create a new Asset group.
    """
    permission_classes = [IsAuthenticated]

    # queryset = AssetGroup.objects.all()
    serializer_class = AssetGroupSerializer

    def get_queryset(self):
        book_id = self.request.query_params.get('book_id')
        queryset = AssetGroup.objects.all()

        if book_id:
            try:
                queryset = queryset.filter(book_id=book_id)
            except Book.DoesNotExist:
                raise ValidationError({"Book not found"})
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Serialize the groups
        serializer = self.get_serializer(queryset, many=True)
        groups = serializer.data

        # Calculate assets, liabilities, and net asset
        assets_liabilities = Asset.objects.filter(group__in=queryset).aggregate(
            assets=Sum(Case(
                When(is_credit=False, then=F('balance')),
                default=0,
                output_field=DecimalField()
            )),
            liabilities=Sum(Case(
                When(is_credit=True, then=F('balance')),
                default=0,
                output_field=DecimalField()
            ))
        )

        assets = assets_liabilities['assets'] or 0
        liabilities = assets_liabilities['liabilities'] or 0
        net_asset = assets + liabilities

        response_data = {
            'groups': groups,
            'assets': assets,
            'liabilities': liabilities,
            'net_asset': net_asset,
        }

        return Response(response_data, status=status.HTTP_200_OK)


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
    serializer_class = AssetSerializer

    def get_queryset(self):
        queryset = Asset.objects.all()
        book_id = self.request.query_params.get('book_id')

        if book_id:
            try:
                # Ensure the book exists
                book = Book.objects.get(id=book_id)
                # Filter assets by asset groups associated with the book
                queryset = queryset.filter(group__book_id=book_id)
            except Book.DoesNotExist:
                raise ValidationError({"detail": "Book not found"})

        return queryset


class AssetDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an Asset instance.
    """
    permission_classes = [IsAuthenticated]

    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
