"""Название коммерческого объекта, заголовок страницы и краткое описание.

Все варианты собираются здесь, чтобы все клиенты показывали их одинаково:
2 типа сделки × (4 типа помещения + «коммерческое помещение») = 10 заголовков."""

CITY_IN = 'в Москве'
MULTIPLE_TYPES = 'коммерческое помещение'
HOUSE = 'д.'
CORPUS = 'корп.'
BUILDING = 'стр.'

COMMERCIAL_TYPE_ACCUSATIVE = {
    'office': 'офисное помещение',
    'retail': 'торговое помещение',
    'warehouse': 'складское помещение',
    'free_use': 'помещение свободного назначения',
}

TRADE_VERB = {'sale': 'Купить', 'rent': 'Снять'}


def format_area(area):
    """140.0 → «140», 60.5 → «60,5»."""
    return f'{area:g}'.replace('.', ',')


def realty_title(realty):
    """«[Тип помещения], [Общая площадь] м²»; у жилой недвижимости — None."""
    if not realty.realty_type.is_commercial:
        return None
    kind = realty.get_commercial_type_display() or realty.realty_type.type
    return f'{kind}, {format_area(realty.about_apartment.area)} м²'


def trade_and_kind(trade_type, commercial_types):
    """«Снять торговое помещение»: что делают с объектом и что это за объект.

    Один тип — он в тексте; ни одного или несколько — «коммерческое
    помещение». Неизвестный тип сделки — None."""
    verb = TRADE_VERB.get(trade_type)
    if verb is None:
        return None
    types = set(commercial_types)
    kind = (
        COMMERCIAL_TYPE_ACCUSATIVE.get(types.pop(), MULTIPLE_TYPES)
        if len(types) == 1
        else MULTIPLE_TYPES
    )
    return f'{verb} {kind}'


def page_title(trade_type, commercial_types):
    """«Снять / Купить [тип помещения] в Москве»."""
    beginning = trade_and_kind(trade_type, commercial_types)
    if beginning is None:
        return None
    return f'{beginning} {CITY_IN}'


def short_address(address):
    """«Ленинский пр-кт, д. 45, корп. 1, стр. А».

    Тип улицы уже внутри названия из справочника, поэтому к нему дописывается
    только дом. Корпус и строение нужны, иначе два разных здания по одному
    номеру дома выглядят одинаково. Улицы в адресе может не быть — тогда
    остаётся один дом. Поле «владение» сюда не идёт: в справочнике им
    описывают форму собственности, а не номер владения."""
    parts = [address.street.name] if address.street_id else []
    parts.append(f'{HOUSE} {address.house_number}')
    for prefix, value in ((CORPUS, address.corpus), (BUILDING, address.building)):
        if value:
            parts.append(f'{prefix} {value}')
    return ', '.join(parts)


def realty_page_title(realty):
    """Заголовок детальной страницы объявления; у жилой недвижимости — None."""
    if not realty.realty_type.is_commercial:
        return None
    types = [realty.commercial_type] if realty.commercial_type else []
    return page_title(realty.trade_type, types)


def realty_short_description(realty):
    """«Снять торговое помещение, 87,9 м², Ленинский пр-кт, д. 1».

    У жилой недвижимости — None, как у названия и заголовка страницы."""
    if not realty.realty_type.is_commercial:
        return None
    types = [realty.commercial_type] if realty.commercial_type else []
    beginning = trade_and_kind(realty.trade_type, types)
    if beginning is None:
        return None
    area = format_area(realty.about_apartment.area)
    return f'{beginning}, {area} м², {short_address(realty.address)}'
