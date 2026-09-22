"""Удаление сообщений и чатов: у каждого участника своя копия переписки.

Регрессия на баг «Удаление сообщений»: удаление у себя не должно задевать
собеседника, объявление можно удалить — чат остается, но писать нельзя.
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from chats.restrictions import SEND_DENIED_REALTY_DELETED
from tests.factories import create_realty, create_user

CHATS_URL = '/api/chats/'
SEND_URL = '/api/chats/send-message/'
SHOW_URL = '/api/chats/show-chat/'
DELETE_CHATS_URL = '/api/chats/delete-chats/'
DELETE_MESSAGES_URL = '/api/chats/delete-messages/'
NEW_MSGS_URL = '/api/users/new-msgs/'
PERSONAL_ACCOUNT_URL = '/api/users/personal-account/'


class ChatDeletionTestBase(TestCase):
    """Переписка из трех сообщений между владельцем и клиентом."""

    def setUp(self):
        self.owner = create_user('chatdelowner')
        self.client_user = create_user('chatdelclient')
        self.realty = create_realty(self.owner)

        self.api = APIClient()

        self.api.force_authenticate(self.client_user)
        self.first_msg_id = self.send(realty_id=self.realty.id, text='Здравствуйте')
        self.second_msg_id = self.send(realty_id=self.realty.id, text='Еще актуально?')

        self.chat_id = self.realty.chats.get().chat_id

        self.api.force_authenticate(self.owner)
        self.answer_msg_id = self.send(chat_id=self.chat_id, text='Да, актуально')

    def send(self, text, realty_id=None, chat_id=None):
        payload = {'message': text}
        if realty_id is not None:
            payload['realty_id'] = realty_id
        if chat_id is not None:
            payload['chat_id'] = chat_id

        response = self.api.post(SEND_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response.data['msg_id']

    def show_chat(self, user):
        """Сообщения чата глазами пользователя."""
        self.api.force_authenticate(user)
        return self.api.post(SHOW_URL, {'chat_id': self.chat_id}, format='json')

    def visible_msg_ids(self, user):
        response = self.show_chat(user)
        if response.status_code == status.HTTP_404_NOT_FOUND:
            return []
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return [msg['msg_id'] for msg in response.data['results']['messages']]

    def chat_ids(self, user):
        self.api.force_authenticate(user)
        response = self.api.get(CHATS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return [chat['chat_id'] for chat in response.data['results']]


class MessageDeletionTest(ChatDeletionTestBase):
    """Удаление отдельных сообщений."""

    def delete_messages(self, user, msg_ids):
        self.api.force_authenticate(user)
        return self.api.post(DELETE_MESSAGES_URL, {'msg_ids': msg_ids}, format='json')

    def test_single_message_is_deleted(self):
        """Удаляется только указанное сообщение, история остается"""
        response = self.delete_messages(self.client_user, [self.first_msg_id])

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['deleted_msg_ids'], [self.first_msg_id])
        self.assertEqual(
            self.visible_msg_ids(self.client_user),
            [self.answer_msg_id, self.second_msg_id],
        )

    def test_deleted_message_stays_for_other_user(self):
        """У собеседника удаленное сообщение остается на месте"""
        self.delete_messages(self.client_user, [self.first_msg_id])

        self.assertEqual(
            sorted(self.visible_msg_ids(self.owner)),
            sorted([self.first_msg_id, self.second_msg_id, self.answer_msg_id]),
        )

    def test_incoming_message_can_be_deleted(self):
        """Удалить можно и входящее сообщение"""
        self.delete_messages(self.client_user, [self.answer_msg_id])

        self.assertNotIn(self.answer_msg_id, self.visible_msg_ids(self.client_user))
        self.assertIn(self.answer_msg_id, self.visible_msg_ids(self.owner))

    def test_several_messages_are_deleted_at_once(self):
        """Пачка сообщений удаляется одним запросом"""
        self.delete_messages(self.client_user, [self.first_msg_id, self.second_msg_id])

        self.assertEqual(self.visible_msg_ids(self.client_user), [self.answer_msg_id])

    def test_foreign_message_is_not_deleted(self):
        """Чужое сообщение удалить нельзя"""
        stranger = create_user('chatdelstranger')

        response = self.delete_messages(stranger, [self.first_msg_id])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(self.first_msg_id, self.visible_msg_ids(self.client_user))

    def test_unknown_message_id_is_rejected(self):
        """Несуществующий msg_id дает 400 и ничего не удаляет"""
        response = self.delete_messages(self.client_user, [self.first_msg_id, 10**6])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(self.first_msg_id, self.visible_msg_ids(self.client_user))

    def test_already_deleted_message_is_rejected(self):
        """Повторное удаление того же сообщения дает 400"""
        self.delete_messages(self.client_user, [self.first_msg_id])

        response = self.delete_messages(self.client_user, [self.first_msg_id])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChatDeletionTest(ChatDeletionTestBase):
    """Удаление чата целиком."""

    def delete_chat(self, user):
        self.api.force_authenticate(user)
        return self.api.post(
            DELETE_CHATS_URL, {'chat_ids': [self.chat_id]}, format='json'
        )

    def test_chat_disappears_only_for_deleting_user(self):
        """Чат удаляется у инициатора и остается у собеседника"""
        response = self.delete_chat(self.client_user)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(self.chat_ids(self.client_user), [])
        self.assertEqual(self.chat_ids(self.owner), [self.chat_id])

    def test_messages_stay_for_other_user(self):
        """У собеседника вся переписка сохраняется"""
        self.delete_chat(self.client_user)

        self.assertEqual(self.visible_msg_ids(self.client_user), [])
        self.assertEqual(len(self.visible_msg_ids(self.owner)), 3)

    def test_new_message_brings_chat_back(self):
        """Новое сообщение возвращает удаленный чат в список"""
        self.delete_chat(self.client_user)

        self.api.force_authenticate(self.owner)
        self.send(chat_id=self.chat_id, text='Вы еще тут?')

        self.assertEqual(self.chat_ids(self.client_user), [self.chat_id])


class UnreadCountersTest(ChatDeletionTestBase):
    """Счетчики в ЛК и в шапке не считают удаленное."""

    def have_new_msgs(self, user):
        self.api.force_authenticate(user)
        response = self.api.get(NEW_MSGS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return response.data['have_new_msgs']

    def new_messages_count(self, user):
        self.api.force_authenticate(user)
        response = self.api.get(PERSONAL_ACCOUNT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return response.data['new_messages_count']

    def test_unread_is_counted_before_deletion(self):
        """Непрочитанное входящее считается"""
        self.assertEqual(self.new_messages_count(self.client_user), 1)
        self.assertTrue(self.have_new_msgs(self.client_user))

    def test_deleted_message_is_not_counted(self):
        """Удаленное входящее не висит значком в шапке"""
        self.api.force_authenticate(self.client_user)
        self.api.post(
            DELETE_MESSAGES_URL, {'msg_ids': [self.answer_msg_id]}, format='json'
        )

        self.assertEqual(self.new_messages_count(self.client_user), 0)
        self.assertFalse(self.have_new_msgs(self.client_user))

    def test_deleted_chat_is_not_counted(self):
        """После удаления чата счетчик обнуляется"""
        self.api.force_authenticate(self.client_user)
        self.api.post(DELETE_CHATS_URL, {'chat_ids': [self.chat_id]}, format='json')

        self.assertEqual(self.new_messages_count(self.client_user), 0)

    def test_chat_list_does_not_mark_messages_read(self):
        """заход в список чатов не гасит непрочитанные сообщения"""
        self.chat_ids(self.client_user)

        self.assertEqual(self.new_messages_count(self.client_user), 1)


class DeletedRealtyChatTest(ChatDeletionTestBase):
    """Объявление удалено: чат остается, писать нельзя."""

    def setUp(self):
        super().setUp()
        self.realty.is_deleted = True
        self.realty.save()

    def test_chat_stays_for_both_users(self):
        """Чат по удаленному объявлению виден обоим участникам"""
        self.assertEqual(self.chat_ids(self.owner), [self.chat_id])
        self.assertEqual(self.chat_ids(self.client_user), [self.chat_id])

    def test_history_is_available(self):
        """Переписка по удаленному объявлению читается"""
        self.assertEqual(len(self.visible_msg_ids(self.client_user)), 3)

    def test_chat_is_marked_as_disabled(self):
        """В чате приходит пометка об удаленном объявлении"""
        response = self.show_chat(self.client_user)
        chat = response.data['results']

        self.assertFalse(chat['can_send'])
        self.assertEqual(chat['disabled_reason'], SEND_DENIED_REALTY_DELETED)
        self.assertTrue(chat['realty']['is_deleted'])

    def test_sending_by_chat_id_is_rejected(self):
        """Отправка по chat_id в удаленное объявление дает 400"""
        self.api.force_authenticate(self.client_user)
        response = self.api.post(
            SEND_URL,
            {'chat_id': self.chat_id, 'message': 'Еще продаете?'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(SEND_DENIED_REALTY_DELETED, str(response.data))

    def test_sending_by_realty_id_is_rejected(self):
        """Отправка по realty_id в удаленное объявление дает 400"""
        stranger = create_user('chatdelbuyer')
        self.api.force_authenticate(stranger)
        response = self.api.post(
            SEND_URL,
            {'realty_id': self.realty.id, 'message': 'Здравствуйте'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(SEND_DENIED_REALTY_DELETED, str(response.data))

    def test_owner_also_cannot_write(self):
        """Владелец в чат по удаленному объявлению тоже не пишет"""
        self.api.force_authenticate(self.owner)
        response = self.api.post(
            SEND_URL,
            {'chat_id': self.chat_id, 'message': 'Объявление снято'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
