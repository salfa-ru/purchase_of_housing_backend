"""Ограничение длины сообщения в чатах — 2500 символов"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from config.constants import MESSAGE_LENGTH
from tests.factories import create_realty, create_user

SEND_URL = '/api/chats/send-message/'


class MessageLengthTest(TestCase):
    """Граница длины на отправке сообщения."""

    def setUp(self):
        self.client = APIClient()
        self.owner = create_user('chatowner')
        self.sender = create_user('chatsender')
        self.realty = create_realty(self.owner)
        self.client.force_authenticate(self.sender)

    def send(self, text):
        return self.client.post(
            SEND_URL,
            {'realty_id': self.realty.id, 'message': text},
            format='json',
        )

    def test_message_of_limit_length_is_accepted(self):
        """Тест: сообщение ровно в 2500 символов проходит"""
        response = self.send('a' * MESSAGE_LENGTH)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cyrillic_message_of_limit_length_is_accepted(self):
        """Тест: 2500 символов кириллицей тоже проходят"""
        response = self.send('я' * MESSAGE_LENGTH)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_longer_message_is_rejected(self):
        """Тест: сообщение длиннее предела отклоняется"""
        response = self.send('a' * (MESSAGE_LENGTH + 1))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)

    def test_error_reports_actual_length(self):
        """Тест: в ошибке указано, сколько символов насчитал сервер"""
        response = self.send('a' * 2643)

        self.assertIn('2643', ' '.join(response.data['message']))
        self.assertIn('2500', ' '.join(response.data['message']))

    def test_short_message_is_accepted(self):
        """Тест: обычное короткое сообщение не задето"""
        response = self.send('Здравствуйте, объявление актуально?')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
