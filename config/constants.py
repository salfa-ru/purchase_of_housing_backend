from datetime import datetime, timedelta

CURRENT_YEAR = datetime.now().year
MIN_YEAR_BUILT = 1500

MIN_ROOM_AREA = 5  # поменять?
MAX_ROOM_AREA = 1500  # поменять?


CHAR_LENGTH = 50

DESCRIPTION_LENGTH = 500
COMPLAINT_LENGTH = 200
NOTIFICATION_LENGTH = {'code': 50, 'part1': 100, 'part2': 200}
QUESTION_LENGTH = 100

NULLABLE_FIELD = {'blank': True, 'null': True}

# min значение цены
MIN_PRICE = 1

# min и max значения этажности
MIN_FLOOR = 1
MAX_FLOOR = 180

# min и max время до метро в мин.
MIN_TIME = 1
MAX_TIME = 60

# тип пользователя для MVP
USER_TYPE_DEFAULT = 'Собственник'

REALTY_STATUS = "На модерации"

# тип жилья для MVP
HOUSING_TYPE = "Вторичное жилье"


# тип продажи для MVP
SALE_TYPE = "Свободная продажа"


# тип сделки
RENT_TRADE_TYPE = 'Аренда'
SALE_TRADE_TYPE = 'Продажа'

# статус объявления
ADVERTISMENT_STATUS = 'Активно'

# допустимые типы для изображений
IMAGE_EXTENSIONS = ('jpg', 'jpeg', 'png')

# максимально допустимый размер для аватара (в Б)
MAX_AVATAR_SIZE = 5 * 1024 * 1024

# длина строки для вывода в str
SHORT_STR_LENGTH = 20


# TODO - После тестирования выставить оптимальное время между показами
# ограничения по частоте обновления счетчиков показов
# для показа полного объявления
COUNTER_FULL_VIEW_MIN_TIME_INTERVAL = timedelta(hours=0, minutes=0, seconds=5)
# для показа объявления в поиске
COUNTER_VIEW_IN_SEARCH_MIN_TIME_INTERVAL = timedelta(hours=0, minutes=0, seconds=5)

# срок жизни объявления, плановое значение - 30 дней
MAX_LISTING_DURATION = timedelta(days=30, hours=0, minutes=0, seconds=0)


class ConstantsAuth:
    """Constants for custom authentication"""

    AUTH_KEY_PATH = 'public_key.pem'
    AUTH_HEADER_PREFIX = b'Bearer'
    TOKEN_AUD = 'example.com'

    HOST = 'http://api.dev.esa.ktsf.ru/'
    URL_REGISTRATION = HOST + 'api/v1/registration/'
    URL_REGISTRATION_PROFILE = HOST + 'api/v1/registration/profile/'
    URL_GET_TOKEN = HOST + 'api/v1/auth/token/'
    URL_GET_PROFILE = HOST + 'api/v1/profile/'
    URL_REFRESH_TOKEN = HOST + '/api/v1/auth/token/refresh/'

    PREFIX_USER_ID_IN_TOKEN = 'user_id'
    PREFIX_UPDATED_DATE_IN_TOKEN = 'pr_up'
