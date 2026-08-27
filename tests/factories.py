"""Общие хелперы для тестов: собирают объекты со всеми обязательными связями."""

from django.contrib.auth import get_user_model

from realty.models import Realty
from realty_addresses.models import Address
from realty_specificities.models import AboutApartment
from realty_values.models import (
    CommunicationMethod,
    RealtyAdvStatus,
    RealtyType,
    RoomsNumber,
    TradeParticipant,
)

User = get_user_model()


def create_user(username, **kwargs):
    """Пользователь с уникальными email и телефоном на основе username."""
    defaults = {
        'password': 'Testpass123',
        'email': f'{username}@test.com',
        'phone_number': f'+7900{abs(hash(username)) % 10**7:07d}',
    }
    defaults.update(kwargs)
    return User.objects.create_user(username=username, **defaults)


def create_realty(owner, realty_type_name='Квартира', realty_type=None, **kwargs):
    """Объявление со всеми обязательными связями."""
    if realty_type is None:
        realty_type, _ = RealtyType.objects.get_or_create(
            type=realty_type_name, defaults={'is_commercial': False}
        )

    owner_type, _ = TradeParticipant.objects.get_or_create(participant='Собственник')
    communication_method, _ = CommunicationMethod.objects.get_or_create(method='Звонок')
    realty_status, _ = RealtyAdvStatus.objects.get_or_create(status='Опубликовано')
    rooms_number, _ = RoomsNumber.objects.get_or_create(number_of_rooms='2')

    address = Address.objects.create(house_number='1', latitude=55.7, longitude=37.6)
    about_apartment = AboutApartment.objects.create(
        number_of_rooms=rooms_number, area=50.0, floor=2, floors_number=9
    )

    return Realty.objects.create(
        owner=owner,
        realty_type=realty_type,
        address=address,
        about_apartment=about_apartment,
        description='Тестовое объявление',
        price=1000000,
        owner_type=owner_type,
        communication_method=communication_method,
        realty_status=realty_status,
        **kwargs,
    )
