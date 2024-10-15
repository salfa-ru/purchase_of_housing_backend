from rest_framework.pagination import PageNumberPagination


class ChatPagination(PageNumberPagination):
    """Пагинатор для переписок в личном кабинете."""
    page_size_query_param = None
    page_size = 10
