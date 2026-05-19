def get_apartment_short_info(realty):
    """Выдача инфо о Realty квартире короткой строкой"""
    number_of_rooms = realty.about_apartment.number_of_rooms.number_of_rooms
    room_suffix = '-комн.' if len(number_of_rooms) <= 2 else ''

    return (
        f'{number_of_rooms}{room_suffix} '
        f'{realty.realty_type.type}, '
        f'{realty.about_apartment.area} м², '
        f'{realty.about_apartment.floor}/{realty.about_apartment.floors_number} этаж'
    )
