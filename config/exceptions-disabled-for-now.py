# myproject/exceptions.py

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.exceptions import AuthenticationFailed, ErrorDetail


def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений для DRF.
    """

    # Сначала вызываем стандартный обработчик DRF
    response = exception_handler(exc, context)

    if response is not None:
        # Общий формат для всех ошибок DRF
        response.data = {
            'status': 'error',
            'code': response.status_code,
            'message': None,  # Инициализируем message как None
            'errors': response.data,  # Включаем оригинальные данные ошибки
        }

        # Специальная обработка AuthenticationFailed
        if isinstance(exc, AuthenticationFailed):
            response.data['message'] = "Authentication failed"
            # Убираем дублирование detail, если оно есть
            if 'detail' in response.data['errors']:
                del response.data['errors']['detail']
            return response

        # Обработка ошибок валидации и других ошибок DRF
        errors = response.data['errors']
        if 'detail' in errors:
            # Если есть detail, используем его как message и удаляем из errors
            response.data['message'] = errors.pop('detail')
        else:
            # Формируем сообщение из словаря ошибок, обходя все поля и сообщения
            error_messages = []
            for field, messages in errors.items():
                for message in messages:
                    # Проверяем, является ли message экземпляром ErrorDetail
                    if isinstance(message, ErrorDetail):
                        error_messages.append(f"{field}: {message}")
                    else:
                        # Если не ErrorDetail, добавляем как есть (на случай нестандартных сообщений)
                        error_messages.append(f"{field}: {message}")
            response.data['message'] = ", ".join(error_messages)

        return response

    else:  # DRF не смог обработать исключение (например, ValueError, TypeError)
        # Обработка исключений, не связанных с DRF
        if isinstance(exc, ValidationError):
            # Ошибки валидации Django (например, в моделях)
            errors = {}
            if hasattr(exc, "message_dict"):
                errors = exc.message_dict
            elif hasattr(exc, 'messages'):
                errors = {"non_field_errors": exc.messages}
            else: # На всякий случай, если нет ни message_dict, ни messages
              errors = {"non_field_errors": [str(exc)]}

            return Response({
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': "Validation Error",
                'errors': errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        elif isinstance(exc, ValueError):  # Пример обработки ValueError
            return Response({
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': 'Invalid input data',
                'errors': {'value_error': [str(exc)]}
            }, status=status.HTTP_400_BAD_REQUEST)

        elif isinstance(exc, TypeError):
            # Ошибка типов
            return Response({
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': 'Type error',
                'errors': {'type_error': [str(exc)]}
            }, status=status.HTTP_400_BAD_REQUEST)

        else:
            # Необработанные исключения - возвращаем 500 Internal Server Error
            # В production, *никогда* не возвращайте подробности необработанных исключений!
            # Записывайте их в лог.
            print(f"Unhandled exception: {exc}")  # Залогируйте ошибку

            return Response({
                'status': 'error',
                'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'message': 'Internal Server Error',
                'errors': {'server_error': ['An unexpected error occurred.']}  # Безопасное сообщение
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)