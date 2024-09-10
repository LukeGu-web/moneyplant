from itertools import chain, groupby
from operator import attrgetter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from record.models import Record, Transfer
from record.serializers import GroupedDaySerializer
from record.pagination import RecordListCreatePagination
from record.filters import CombinedFilter


class CombinedListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = RecordListCreatePagination
    serializer_class = GroupedDaySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CombinedFilter
    search_fields = ['note', 'amount', 'category', 'subcategory']

    def get_queryset(self):
        user = self.request.user
        book_id = self.request.query_params.get('book_id')
        asset_ids = self.request.query_params.getlist('asset')

        records = Record.objects.filter(book__user=user, book__id=book_id)
        transfers = Transfer.objects.filter(book__user=user, book__id=book_id)

        if asset_ids:
            records = records.filter(asset__id__in=asset_ids)
            transfers = transfers.filter(
                Q(from_asset__id__in=asset_ids) | Q(to_asset__id__in=asset_ids)
            )

        # Apply filters
        combined_filter = self.filterset_class(
            self.request.GET, queryset=records)
        filtered_records = combined_filter.qs

        # Handle 'type' filter for transfers
        type_filter = self.request.query_params.get('type')
        if type_filter and type_filter != 'transfer':
            transfers = Transfer.objects.none()

        # Handle 'is_marked_tax_return' filter
        is_marked_tax_return = self.request.query_params.get(
            'is_marked_tax_return')
        if is_marked_tax_return == 'true':
            transfers = Transfer.objects.none()

        # Apply search
        search_query = self.request.query_params.get('search')
        if search_query:
            filtered_records = filtered_records.filter(
                Q(note__icontains=search_query) |
                Q(amount__icontains=search_query) |
                Q(category__icontains=search_query) |
                Q(subcategory__icontains=search_query)
            )
            transfers = transfers.filter(
                Q(note__icontains=search_query) |
                Q(amount__icontains=search_query)
            )

        # Filter transfers based on date range if provided
        date_after = self.request.query_params.get('date_after')
        date_before = self.request.query_params.get('date_before')
        if date_after:
            transfers = transfers.filter(date__gte=date_after)
        if date_before:
            transfers = transfers.filter(date__lte=date_before)

        # Combine and sort the querysets
        combined = sorted(
            chain(filtered_records, transfers),
            key=attrgetter('date'),
            reverse=True
        )

        # Group by date
        grouped_data = []
        for date, group in groupby(combined, key=lambda x: x.date.date()):
            group_list = list(group)
            sum_of_income = sum(r.amount for r in group_list if isinstance(
                r, Record) and r.type == 'income')
            sum_of_expense = sum(r.amount for r in group_list if isinstance(
                r, Record) and r.type == 'expense')

            grouped_data.append({
                'date': date,
                'records': group_list,
                'sum_of_income': sum_of_income,
                'sum_of_expense': sum_of_expense
            })

        return grouped_data

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
