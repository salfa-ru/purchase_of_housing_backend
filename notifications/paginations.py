from config.pagination import BasePagination


class NotificationPagination(BasePagination):
    """Уведомления в личном кабинете: размер страницы фиксированный."""

    page_size_query_param = None
    page_size = 10
