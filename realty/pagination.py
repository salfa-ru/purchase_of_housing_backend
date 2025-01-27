from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict
from config import constants


class LimitRealtyPagination(PageNumberPagination):
    """Custom pagination for Realty queryset."""
    page_size_query_param = None
    page_size = 10


class MyRealtyPagination(PageNumberPagination):
    """Custom pagination for my Realty queryset для ЛИЧНОГО КАБИНЕТА."""

    page_size_query_param = 'page_size'

    def get_page_size(self, request):

        def_page_size = constants.MY_REALTY_PAGESIZE_DEFAULT
        max_page_size = constants.MY_REALTY_PAGESIZE_MAX

        if self.page_size_query_param:
            try:
                page_size = int(request.query_params.get(self.page_size_query_param, def_page_size))
                if page_size > max_page_size:
                    raise ValidationError(
                        f'Максимальное количество объявлений на странице: {max_page_size}'
                    )
                return page_size
            except ValueError:
                return def_page_size
        return def_page_size

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),  # Общее количество объектов
            ('pages_total', self.page.paginator.num_pages),  # Общее количество страниц
            ('page_size', self.get_page_size(self.request)),  # Количество объявлений на странице
            ('current_page', self.page.number),  # Текущая страница
            ('next', self.get_next_link()),  # URL следующей страницы
            ('previous', self.get_previous_link()),  # URL предыдущей страницы
            ('results', data)  # Данные текущей страницы
        ]))

    # Старая Пагинация (Кости), выдавала 3 или 4 на странице
    # Филипп: я вообще не понимаю логики 3/4, причем активных объявлений
    # from realty.models import Realty
    # def get_page_size(self, request):
    #     owner = request.user
    #     active_realties_count = Realty.objects.filter(
    #         owner=owner,
    #         realty_status__status='Активно').count()
    #     print(active_realties_count)
    #     if active_realties_count <= 1:
    #         return 4
    #     elif active_realties_count > 2:
    #         return 3
    #     return 4
