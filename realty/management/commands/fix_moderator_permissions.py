from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from chats.models import Message
from realty.models import Realty
from users.models import User


class Command(BaseCommand):
    help = (
        'Создаем/проверяем группу ALFA Moderators, обновляем этой группе права, '
        'и создаем/проверяем первого модератора (привязанного к email: '
        'moderator@moderator.ru'
    )

    def handle(self, *args, **options):
        try:
            group, created = Group.objects.get_or_create(name='ALFA Moderators')
            if not created:
                group.permissions.clear()

            content_types = ContentType.objects.all()
            view_permissions = Permission.objects.filter(
                content_type__in=content_types, codename__icontains='view'
            )
            group.permissions.add(*view_permissions)
            self.stdout.write(
                self.style.HTTP_INFO('Добавлены права на просмотр всех таблиц')
            )

            realty_content_type = ContentType.objects.get_for_model(Realty)
            realty_permissions = Permission.objects.filter(
                content_type=realty_content_type,
                codename__in=['view_realty', 'change_realty'],
            )

            group.permissions.add(*realty_permissions)
            self.stdout.write(self.style.HTTP_INFO('Добавлены права на Realty:'))
            self.stdout.write(self.style.HTTP_SUCCESS(f'{realty_permissions}'))

            message_content_type = ContentType.objects.get_for_model(Message)
            message_permissions = Permission.objects.filter(
                content_type=message_content_type,
            )
            group.permissions.add(*message_permissions)
            self.stdout.write(self.style.HTTP_INFO('Добавлены права на Сообщения: '))
            self.stdout.write(self.style.HTTP_SUCCESS(f'{message_permissions}'))

            django_q_content_types = ContentType.objects.filter(app_label='django_q')
            django_q_permissions = Permission.objects.filter(
                content_type__in=django_q_content_types
            )
            group.permissions.remove(*django_q_permissions)
            self.stdout.write(self.style.HTTP_INFO('Убраны права на DJANQO-Q:'))
            self.stdout.write(self.style.HTTP_SUCCESS(f'{django_q_permissions}'))

            user, user_created = User.objects.update_or_create(
                email='moderator@moderator.ru',
                defaults={
                    'first_name': 'moderator',
                    'last_name': 'moderator',
                    'is_active': True,
                    'is_staff': True,
                    'phone_number': '112',
                },
            )

            user.username = 'moderator'
            user.password = 'moderator'
            user.save(update_fields=['username', 'password'])

            if user_created:
                self.stdout.write(
                    self.style.SUCCESS("Создан пользователь 'moderator'.")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("Пользователь 'moderator' обновлен.")
                )

            group.user_set.add(user)

            self.stdout.write(
                self.style.SUCCESS(
                    'Права группы ALFA Moderators обновлены, модератор (уже) '
                    'существует.'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Ошибка при создании/обновлении '
                    f"группы ALFA Moderators или пользователя 'moderator': {e}"
                )
            )
