"""Название коммерческого объекта и заголовок страницы.

Все варианты собираются здесь, чтобы все клиенты показывали их одинаково:
2 типа сделки × (4 типа помещения + «коммерческое помещение») = 10 заголовков."""

CITY_IN = 'в Москве'
MULTIPLE_TYPES = 'коммерческое помещение'

COMMERCIAL_TYPE_ACCUSATIVE = {
    'office': 'офис',
    'retail': 'торговое помещение',
    'warehouse': 'склад',
    'free_use': 'помещение свободного назначения',
}

TRADE_VERB = {'sale': 'Купить', 'rent': 'Снять'}


def format_area(area):
    """140.0 → «140», 60.5 → «60.5»."""
    return f'{area:g}'


def realty_title(realty):
    """«[Тип помещения], [Общая площадь] м²»; у жилой недвижимости — None."""
    if not realty.realty_type.is_commercial:
        return None
    kind = realty.get_commercial_type_display() or realty.realty_type.type
    return f'{kind}, {format_area(realty.about_apartment.area)} м²'


def page_title(trade_type, commercial_types):
    """«Снять / Купить [тип помещения] в Москве».

    Один тип — он в заголовке; ни одного или несколько — «коммерческое
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
    return f'{verb} {kind} {CITY_IN}'


def realty_page_title(realty):
    """Заголовок детальной страницы объявления; у жилой недвижимости — None."""
    if not realty.realty_type.is_commercial:
        return None
    types = [realty.commercial_type] if realty.commercial_type else []
    return page_title(realty.trade_type, types)
