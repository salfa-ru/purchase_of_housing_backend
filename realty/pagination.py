from rest_framework.pagination import PageNumberPagination

from realty.models import Realty


class LimitRealtyPagination(PageNumberPagination):
    """Custom pagination for Realty queryset."""
    page_size_query_param = None
    page_size = 10


class MyRealtyPagination(PageNumberPagination):
    """Custom pagination for my Realty queryset in personal account."""

    def get_page_size(self, request):
        owner = request.user
        active_realties_count = Realty.objects.filter(
            owner=owner,
            realty_status__status='Активно').count()
        print(active_realties_count)
        if active_realties_count <= 1:
            return 4
        elif active_realties_count > 2:
            return 3
        return 4
