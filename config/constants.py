from datetime import datetime


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

# min и max время до метро в мин.
MIN_TIME = 1
MAX_TIME = 60

# тип пользователя для MVP
USER_TYPE_DEFAULT = 'Собственник'

# тип сделки
RENT_TRADE_TYPE = 'Аренда'
SALE_TRADE_TYPE = 'Продажа'

# статус объявления
ADVERTISMENT_STATUS = 'Активно'

# тип санузла
SEPARATE_BATHROOM = 'Раздельный'
COMBINED_BATHROOM = 'Совмещенный'


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
