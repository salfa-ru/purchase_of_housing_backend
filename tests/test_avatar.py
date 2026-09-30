"""Загрузка и удаление аватарки: форматы, размер, разрешение, тексты ошибок."""

import io
import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from config.constants import MAX_AVATAR_SIZE
from tests.factories import create_user
from users.validators import (
    AVATAR_SINGLE_FILE,
    AVATAR_TOO_LARGE,
    AVATAR_WRONG_FORMAT,
)

AVATAR_URL = '/api/users/me/avatar/'


def make_heavy_image(name='big.png'):
    """Картинка заведомо больше допустимого размера."""
    side = 1500
    image = Image.frombytes('RGB', (side, side), os.urandom(side * side * 3))
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type='image/png')


def make_image(name='avatar.jpg', size=(200, 200), image_format='JPEG'):
    """Картинка заданного размера в виде загружаемого файла."""
    buffer = io.BytesIO()
    Image.new('RGB', size, color='green').save(buffer, format=image_format)
    buffer.seek(0)
    content_type = f'image/{image_format.lower()}'
    return SimpleUploadedFile(name, buffer.read(), content_type=content_type)


class AvatarUploadTest(TestCase):
    """Загрузка аватарки."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user('avatarowner')
        self.client.force_authenticate(self.user)

    def upload(self, avatar):
        return self.client.patch(AVATAR_URL, {'avatar': avatar}, format='multipart')

    def test_jpg_is_accepted(self):
        """Обычная картинка загружается"""
        response = self.upload(make_image())

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.avatar)

    def test_webp_is_accepted(self):
        """Формат webp разрешен для аватарки"""
        response = self.upload(make_image('avatar.webp', image_format='WEBP'))

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_text_file_is_rejected(self):
        """Текстовый файл отклоняется с перечнем форматов"""
        wrong = SimpleUploadedFile('notes.txt', b'just text', content_type='text/plain')

        response = self.upload(wrong)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(AVATAR_WRONG_FORMAT, response.data['avatar'])

    def test_too_large_file_is_rejected(self):
        """Файл больше пяти мегабайт отклоняется с понятным текстом"""
        heavy = make_heavy_image()
        self.assertGreater(heavy.size, MAX_AVATAR_SIZE)

        response = self.upload(heavy)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(AVATAR_TOO_LARGE, response.data['avatar'])

    def test_two_files_are_rejected(self):
        """Два файла в одном запросе отклоняются"""
        response = self.client.patch(
            AVATAR_URL,
            {'avatar': [make_image('one.jpg'), make_image('two.jpg')]},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(AVATAR_SINGLE_FILE, response.data['avatar'])

    def test_small_image_is_rejected(self):
        """Картинка меньше ста пикселей отклоняется"""
        response = self.upload(make_image('small.jpg', size=(50, 50)))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('avatar', response.data)

    def test_anonymous_cannot_upload(self):
        """Без авторизации аватарку не загрузить"""
        self.client.force_authenticate(None)

        response = self.upload(make_image())

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AvatarDeleteTest(TestCase):
    """Удаление аватарки."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user('avatardeleter')
        self.client.force_authenticate(self.user)

    def test_avatar_is_deleted(self):
        """Загруженная аватарка удаляется"""
        self.client.patch(AVATAR_URL, {'avatar': make_image()}, format='multipart')

        response = self.client.delete(AVATAR_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.user.refresh_from_db()
        self.assertFalse(self.user.avatar)

    def test_delete_without_avatar_gives_404(self):
        """Удаление несуществующей аватарки дает 404"""
        response = self.client.delete(AVATAR_URL)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
