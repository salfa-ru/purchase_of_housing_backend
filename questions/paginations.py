from config import constants
from config.pagination import BasePagination


class QuestionsPagination(BasePagination):
    """Разделы и вопросы справочника."""

    page_size = constants.QUESTIONS_PAGESIZE_DEFAULT
    max_page_size = constants.QUESTIONS_PAGESIZE_MAX
