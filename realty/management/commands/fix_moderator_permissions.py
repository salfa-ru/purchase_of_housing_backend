from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from realty.models import Realty
from users.models import User

# TODO - Уточнить, к каким таблицам совсем убрать доступ Модераторам, а к каким, наоборот, открыть.
# TODO - В Продакшене убрать пользователя Moderator, или хотя бы поменять пароль и email.

class Command(BaseCommand):
    help = ('Создаем/проверяем группу ALFA Moderators, обновляем этой группе права, '
            'и создаем/проверяем первого модератора (привязанного к email: moderator@moderator.ru')

    def handle(self, *args, **options):
        try:
            # 1. Работа с группой
            group, created = Group.objects.get_or_create(name='ALFA Moderators')
            if not created:
                group.permissions.clear()  # Очищаем права, если группа уже существовала

            # Добавляем права на просмотр всех таблиц
            content_types = ContentType.objects.all()
            view_permissions = Permission.objects.filter(content_type__in=content_types, codename__icontains='view')
            group.permissions.add(*view_permissions)

            # Добавляем права view и change на таблицу Realty
            realty_content_type = ContentType.objects.get_for_model(Realty)
            realty_permissions = Permission.objects.filter(
                content_type=realty_content_type,
                codename__in=['view_realty', 'change_realty']
            )
            group.permissions.add(*realty_permissions)

            # 2. Работа с пользователем
            user, user_created = User.objects.update_or_create(
                email='moderator@moderator.ru',
                defaults={
                    'first_name': 'moderator',
                    'last_name': 'moderator',
                    'is_active': True,
                    'is_staff': True,
                    'phone_number': '112',
                }
            )

            # Установка стандартного имени пользователя и пароля
            user.username = 'moderator'
            user.password = 'moderator'  # Set username after initial save
            user.save(update_fields=['username', 'password'])  # Save username and password only

            if user_created:
                self.stdout.write(self.style.SUCCESS("Создан пользователь 'moderator'."))
            else:
                self.stdout.write(self.style.SUCCESS("Пользователь 'moderator' обновлен."))

            # Добавляем пользователя в группу ALFA Moderators (если он еще не там)
            group.user_set.add(user)

            self.stdout.write(self.style.SUCCESS('Права группы ALFA Moderators обновлены, модератор (уже) существует.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при создании/обновлении "
                                               f"группы ALFA Moderators или пользователя 'moderator': {e}"))