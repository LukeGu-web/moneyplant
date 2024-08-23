from rest_framework.pagination import PageNumberPagination


class RecordListCreatePagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "size"
    max_page_size = 200
