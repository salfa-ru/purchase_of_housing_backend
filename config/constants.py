import os
from datetime import UTC, datetime, timedelta

CURRENT_YEAR = datetime.now(UTC).year


MIN_YEAR_BUILT = 1500

MIN_ROOM_AREA = 5
MAX_ROOM_AREA = 1500

NUMBER_OF_PHOTOS_MIN = 1
NUMBER_OF_PHOTOS_MAX = 5

CHAR_LENGTH = 50
NAME_LENGTH = 40

DESCRIPTION_LENGTH = 2000
COMPLAINT_LENGTH = 200
NOTIFICATION_LENGTH = {'code': 50, 'part1': 100, 'part2': 200}
DEVICE_TOKEN_LENGTH = 255
QUESTION_LENGTH = 100
MESSAGE_LENGTH = 2500

NULLABLE_FIELD = {'blank': True, 'null': True}

MIN_PRICE = 1

MIN_FLOOR = 1
MAX_FLOOR = 180

MIN_TIME = 1
MAX_TIME = 60

USER_TYPE_DEFAULT = 'Собственник'

REALTY_STATUS = 'На модерации'

HOUSING_TYPE = 'Вторичное жилье'


SALE_TYPE = 'Свободная продажа'


RENT_TRADE_TYPE = 'Аренда'
SALE_TRADE_TYPE = 'Продажа'

ADVERTISMENT_STATUS = 'Активно'

# id статусов объявления в справочнике RealtyAdvStatus
STATUS_ACTIVE_ID = 1
STATUS_ON_MODERATION_ID = 2
STATUS_REJECTED_ID = 3
STATUS_ARCHIVED_ID = 4

IMAGE_EXTENSIONS = ('jpg', 'jpeg', 'png')
AVATAR_EXTENSIONS = ('jpg', 'jpeg', 'png', 'webp')

MAX_AVATAR_SIZE = 5 * 1024 * 1024

MIN_AVATAR_WIDTH = 100
MIN_AVATAR_HEIGHT = 100

SHORT_STR_LENGTH = 20

MAX_MINUTES_TO_METRO = 180

COUNTER_FULL_VIEW_MIN_TIME_INTERVAL = timedelta(hours=0, minutes=0, seconds=5)
COUNTER_VIEW_IN_SEARCH_MIN_TIME_INTERVAL = timedelta(hours=0, minutes=0, seconds=5)


def parse_dd_hh_mm_ss(val):
    d, h, m, s = (int(x) for x in val.split(':'))
    return timedelta(days=d, hours=h, minutes=m, seconds=s)


MAX_LISTING_DURATION_raw = os.getenv('MAX_LISTING_DURATION_DD_HH_MM_SS')

MAX_LISTING_DURATION = (
    parse_dd_hh_mm_ss(MAX_LISTING_DURATION_raw)
    if MAX_LISTING_DURATION_raw
    else timedelta(days=30)
)

MY_REALTY_PAGESIZE_DEFAULT = 10
MY_REALTY_PAGESIZE_MAX = 50

LATEST_REALTY_LIMIT_DEFAULT = 3
LATEST_REALTY_LIMIT_MAX = 100

BATCH_IDS_MAX = 100

FAVORITES_PAGESIZE_DEFAULT = 4

CHATS_PAGESIZE_DEFAULT = 10
CHATS_PAGESIZE_MAX = 50
MESSAGES_PAGESIZE_DEFAULT = 10
MESSAGES_PAGESIZE_MAX = 50

QUESTIONS_PAGESIZE_DEFAULT = 10
QUESTIONS_PAGESIZE_MAX = 50


class ConstantsAuth:
    """Константы своей аутентификации."""

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
