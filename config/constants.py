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
