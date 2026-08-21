from django.db import DataError, IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def db_error_exception_handler(exc, context):
    """
    Штатный обработчик DRF + перевод ошибок БД в 400 вместо 500."""
    response = exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, DataError | IntegrityError):
        return Response(
            {'detail': 'Переданные данные не соответствуют ограничениям базы данных.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return None
