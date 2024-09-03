from rest_framework.pagination import PageNumberPagination


class LimitRealtyPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 10


class LimitShortRealtyPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 3
    max_page_size = 3
