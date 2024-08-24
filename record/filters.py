import django_filters
from django.db.models import Q
from .models import Record, Transfer


class CombinedFilter(django_filters.FilterSet):
    type = django_filters.CharFilter(method='filter_type')
    is_marked_tax_return = django_filters.BooleanFilter(
        method='filter_is_marked_tax_return')
    category = django_filters.CharFilter(method='filter_category')
    date_after = django_filters.DateFilter(
        field_name='date', lookup_expr='gte')
    date_before = django_filters.DateFilter(
        field_name='date', lookup_expr='lte')

    def filter_type(self, queryset, name, value):
        return queryset.filter(Q(type=value) | Q(type='transfer'))

    def filter_is_marked_tax_return(self, queryset, name, value):
        return queryset.filter(Q(is_marked_tax_return=value) | Q(type='transfer'))

    def filter_category(self, queryset, name, value):
        return queryset.filter(Q(category=value) | Q(type='transfer'))

    class Meta:
        model = Record
        fields = ['type', 'is_marked_tax_return',
                  'category', 'date_after', 'date_before']