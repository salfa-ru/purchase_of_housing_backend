from rest_framework.pagination import PageNumberPagination


class LimitRealtyPagination(PageNumberPagination):
    """Custom pagination for Realty queryset."""
    page_size_query_param = None
    page_size = 10
