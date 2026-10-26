def get_apartment_short_info(realty):
    """Выдача инфо о Realty квартире короткой строкой"""
    apartment = realty.about_apartment
    rooms = apartment.number_of_rooms
    rooms_prefix = ''
    if rooms:
        number_of_rooms = rooms.number_of_rooms
        room_suffix = '-комн.' if len(number_of_rooms) <= 2 else ''
        rooms_prefix = f'{number_of_rooms}{room_suffix} '

    return (
        f'{rooms_prefix}'
        f'{realty.realty_type.type}, '
        f'{apartment.area} м², '
        f'{apartment.floor or "—"}/{apartment.floors_number} этаж'
    )
