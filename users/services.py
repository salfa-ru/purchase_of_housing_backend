import requests

from rest_framework import exceptions
from config.constants import ConstantsAuth
from users.models import User


def create_user_from_esa(user_id, token):
    """Получаем профиль пользователя из ЕСА, создаем у себя в базе"""

    user_data = get_profile_from_esa(token)

    User.objects.create(
        uuid_esa=user_id,
        # TODO заменить на login, когда появится в ЕСА
        username=user_data.get('email'),
        first_name=user_data.get('first_name'),
        last_name=user_data.get('last_name'),
        phone_number=user_data.get('phone'),
        email=user_data.get('email'),
        updated_at=user_data.get('updated_at'),
    )


def update_user_from_esa(user, token):
    """Получаем профиль пользователя из ЕСА, обновляем данные у себя в базе"""

    user_data = get_profile_from_esa(token)

    # TODO заменить на login, когда появится в ЕСА
    user.username = user_data.get('email')
    user.first_name = user_data.get('first_name')
    user.last_name = user_data.get('last_name')
    user.phone_number = user_data.get('phone')
    user.email = user_data.get('email')
    user.updated_at = user_data.get('updated_at')

    user.save()


def get_profile_from_esa(token):
    """Get user profile from ESA"""

    headers = {'Authorization': 'Bearer ' + token.decode('ascii')}
    try:
        responce = requests.get(ConstantsAuth.URL_GET_PROFILE, headers=headers)
    except requests.exceptions.RequestException as e:
        msg = f'In ESA profile RequestException: {e}'
        raise exceptions.AuthenticationFailed(detail=msg)

    if not check_esa_fields(responce.json()):
        msg = f'In ESA profile wrong fields'
        raise exceptions.AuthenticationFailed(detail=msg)

    return responce.json()


def check_esa_fields(user_data):
    """Проверяем, что при получении профиля все поля пришли из ЕСА"""

    # TODO добавить login, когда появится в ЕСА
    return (user_data.get('email')
            and user_data.get('first_name')
            and user_data.get('last_name')
            and user_data.get('phone')
            and user_data.get('email')
            and user_data.get('updated_at'))
