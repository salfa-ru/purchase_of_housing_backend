from rest_framework.pagination import PageNumberPagination


class NotificationPagination(PageNumberPagination):
    """Пагинатор для уведомлений в личном кабинете."""
    page_size_query_param = None
    page_size = 10
