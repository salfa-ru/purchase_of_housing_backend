from rest_framework.exceptions import ValidationError

PAGE_SIZE_ERROR = 'Должно быть положительным целым числом.'


class StrictPageSizeMixin:
    """Строгая проверка параметра page_size."""

    def get_page_size(self, request):
        if not self.page_size_query_param:
            return self.page_size

        if self.page_size_query_param not in request.query_params:
            return self.page_size

        raw = request.query_params[self.page_size_query_param]
        try:
            page_size = int(raw)
        except (TypeError, ValueError) as err:
            raise ValidationError(
                {self.page_size_query_param: PAGE_SIZE_ERROR}
            ) from err

        if page_size <= 0:
            raise ValidationError({self.page_size_query_param: PAGE_SIZE_ERROR})

        if self.max_page_size and page_size > self.max_page_size:
            raise ValidationError(
                {
                    self.page_size_query_param: (
                        f'Не должно превышать {self.max_page_size}.'
                    )
                }
            )
        return page_size
