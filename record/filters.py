import django_filters
from django.db.models import Q
from .models import Record, Transfer


class CombinedFilter(django_filters.FilterSet):
    type = django_filters.CharFilter(method='filter_type')
    is_marked_tax_return = django_filters.BooleanFilter(
        method='filter_is_marked_tax_return')
    date_after = django_filters.DateFilter(
        field_name='date', lookup_expr='gte')
    date_before = django_filters.DateFilter(
        field_name='date', lookup_expr='lte')

    def filter_type(self, queryset, name, value):
        if value == 'transfer':
            return queryset.filter(Q(type='transfer') | Q(id__in=Transfer.objects.values('id')))
        else:
            return queryset.filter(type=value)

    def filter_is_marked_tax_return(self, queryset, name, value):
        return queryset.filter(Q(is_marked_tax_return=value) | Q(type='transfer'))

    class Meta:
        model = Record
        fields = ['type', 'is_marked_tax_return', 'date_after', 'date_before']
