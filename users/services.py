import requests

from rest_framework import exceptions
from config.constants import ConstantsAuth
from users.models import User


def create_user_from_esa(user_id, token):
    """Получаем профиль пользователя из ЕСА, создаем у себя в базе"""

    user_data = get_profile_from_ESA(token)

    user = User.objects.create(
        id=user_id,
        # TODO заменить на login, когда появитя в ЕСА
        username=user_data.get('email'),
        first_name=user_data.get('first_name'),
        last_name=user_data.get('last_name'),
        birthday=user_data.get('birthday'),
        phone_number=user_data.get('phone'),
        email=user_data.get('email'),
    )
    return user


# TODO заготовка. Проверить
def update_user_from_esa(user, token):
    """Получаем профиль пользователя из ЕСА, обновляем данные у себя в базе"""

    user_data = get_profile_from_ESA(token)

    # TODO заменить на login, когда появитя в ЕСА
    user.username = user_data.get('email')
    user.first_name = user_data.get('first_name'),
    user.last_name = user_data.get('last_name'),
    user.birthday = str(user_data.get('birthday')),
    user.phone_number = user_data.get('phone'),
    user.email = user_data.get('email'),

    user.save()


def get_profile_from_ESA(token):
    """Get user profile from ESA"""

    headers = {'Authorization': 'Bearer ' + token.decode('ascii')}
    try:
        responce = requests.get(ConstantsAuth.URL_GET_PROFILE, headers=headers)
    except requests.exceptions.RequestException as e:
        msg = f'In ESA profile RequestException: {e}'
        raise exceptions.AuthenticationFailed(detail=msg)

    return responce.json()
