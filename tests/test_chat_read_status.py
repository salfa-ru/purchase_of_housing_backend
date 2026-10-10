"""Прочитанными становятся только сообщения, попавшие на страницу."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from chats.models import Message
from config import constants
from tests.factories import create_realty, create_user

CHATS_URL = '/api/chats/'
SEND_URL = '/api/chats/send-message/'
SHOW_URL = '/api/chats/show-chat/'

INCOMING_COUNT = 15


class ChatReadStatusTest(TestCase):
    """Клиент пишет владельцу 15 сообщений, владелец открывает чат."""

    def setUp(self):
        self.owner = create_user('readowner')
        self.client_user = create_user('readclient')
        self.realty = create_realty(self.owner)
        self.api = APIClient()

        self.api.force_authenticate(self.client_user)
        for number in range(INCOMING_COUNT):
            self.send({'realty_id': self.realty.id}, f'Сообщение {number}')
        self.chat_id = self.realty.chats.get().chat_id

    def send(self, target, text):
        response = self.api.post(SEND_URL, {'message': text, **target}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def show_chat(self, user, **params):
        self.api.force_authenticate(user)
        query = ''.join(f'&{key}={value}' for key, value in params.items())
        response = self.api.post(
            f'{SHOW_URL}?{query.lstrip("&")}', {'chat_id': self.chat_id}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return response.data['results']['messages']

    def unread_in_db(self, user):
        return Message.objects.filter(user_to=user, is_new=True).count()

    def test_first_page_marks_only_shown_messages(self):
        """Первая страница помечает прочитанными только свои сообщения"""
        shown = self.show_chat(self.owner)

        self.assertEqual(len(shown), constants.MESSAGES_PAGESIZE_DEFAULT)
        self.assertEqual(
            self.unread_in_db(self.owner),
            INCOMING_COUNT - constants.MESSAGES_PAGESIZE_DEFAULT,
        )
        shown_ids = [message['msg_id'] for message in shown]
        self.assertFalse(
            Message.objects.filter(msg_id__in=shown_ids, is_new=True).exists()
        )

    def test_second_page_reads_the_rest(self):
        """Вторая страница дочитывает оставшиеся сообщения"""
        self.show_chat(self.owner)
        shown = self.show_chat(self.owner, page=2)

        self.assertEqual(
            len(shown), INCOMING_COUNT - constants.MESSAGES_PAGESIZE_DEFAULT
        )
        self.assertEqual(self.unread_in_db(self.owner), 0)

    def test_large_page_reads_everything(self):
        """Страница, вместившая все сообщения, помечает их все"""
        self.show_chat(self.owner, page_size=constants.MESSAGES_PAGESIZE_MAX)
        self.assertEqual(self.unread_in_db(self.owner), 0)

    def test_new_messages_are_flagged_in_response(self):
        """В ответе только что прочитанные сообщения ещё отмечены новыми"""
        shown = self.show_chat(self.owner)
        self.assertTrue(all(message['is_new'] for message in shown))

        shown_again = self.show_chat(self.owner)
        self.assertFalse(any(message['is_new'] for message in shown_again))

    def test_sender_does_not_read_own_messages(self):
        """Отправитель, открыв чат, не помечает свои сообщения прочитанными"""
        self.show_chat(self.client_user, page_size=constants.MESSAGES_PAGESIZE_MAX)
        self.assertEqual(self.unread_in_db(self.owner), INCOMING_COUNT)

    def test_unread_counter_in_chat_list(self):
        """Счётчик непрочитанных в списке чатов учитывает только страницу"""
        self.show_chat(self.owner)

        self.api.force_authenticate(self.owner)
        response = self.api.get(CHATS_URL)
        chat = response.data['results'][0]

        self.assertEqual(
            chat['unread'], INCOMING_COUNT - constants.MESSAGES_PAGESIZE_DEFAULT
        )
        self.assertEqual(
            response.data['unread_total'],
            INCOMING_COUNT - constants.MESSAGES_PAGESIZE_DEFAULT,
        )
