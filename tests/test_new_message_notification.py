"""Уведомление получателю при новом сообщении в чате."""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from notifications.constants import NEW_MESSAGE_CODE
from notifications.models import Notification, NotificationTemplate
from tests.factories import create_realty, create_user

SEND_URL = '/api/chats/send-message/'
NOTIFICATIONS_URL = '/api/notifications/'


class NewMessageNotificationTest(TestCase):
    """Сообщение в чате порождает уведомление для получателя."""

    def setUp(self):
        self.client = APIClient()
        self.owner = create_user('notifyowner')
        self.sender = create_user('notifysender')
        self.realty = create_realty(self.owner)

    def send(self, text='Здравствуйте', user=None):
        self.client.force_authenticate(user or self.sender)
        return self.client.post(
            SEND_URL,
            {'realty_id': self.realty.id, 'message': text},
            format='json',
        )

    def notifications_of(self, user):
        self.client.force_authenticate(user)
        response = self.client.get(NOTIFICATIONS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return response.data['results']

    def test_recipient_gets_notification(self):
        """Владелец объявления получает уведомление о новом сообщении"""
        response = self.send()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(
            Notification.objects.filter(
                user_to=self.owner, template__code=NEW_MESSAGE_CODE
            ).count(),
            1,
        )

    def test_sender_gets_nothing(self):
        """Отправителю уведомление не создается"""
        self.send()

        self.assertFalse(Notification.objects.filter(user_to=self.sender).exists())

    def test_notification_is_bound_to_realty(self):
        """Уведомление привязано к объявлению из чата"""
        self.send()

        notification = Notification.objects.get(user_to=self.owner)
        self.assertEqual(notification.realty, self.realty)
        self.assertTrue(notification.is_new)

    def test_notification_text_contains_realty_number(self):
        """В тексте уведомления подставлен номер объявления"""
        self.send()

        notification = self.notifications_of(self.owner)[0]

        self.assertIn(f'№{self.realty.id}', notification['template']['part1'])
        self.assertEqual(
            notification['template']['part2'], 'Откройте чат, чтобы прочитать.'
        )

    def test_answer_notifies_the_other_side(self):
        """Ответ владельца уведомляет клиента, а не владельца"""
        self.send()
        chat_id = self.realty.chats.get().chat_id

        self.client.force_authenticate(self.owner)
        response = self.client.post(
            SEND_URL, {'chat_id': chat_id, 'message': 'Да'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Notification.objects.filter(user_to=self.sender).count(), 1)
        self.assertEqual(Notification.objects.filter(user_to=self.owner).count(), 1)

    def test_every_message_creates_notification(self):
        """Каждое сообщение дает свое уведомление"""
        self.send('Первое')
        self.send('Второе')

        self.assertEqual(Notification.objects.filter(user_to=self.owner).count(), 2)

    def test_message_is_sent_even_without_template(self):
        """Без шаблона в базе сообщение все равно отправляется"""
        NotificationTemplate.objects.filter(code=NEW_MESSAGE_CODE).delete()

        with self.assertLogs('notifications.utils', level='ERROR'):
            response = self.send()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertFalse(Notification.objects.exists())
