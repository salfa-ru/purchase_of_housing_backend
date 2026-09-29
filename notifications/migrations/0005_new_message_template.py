from django.db import migrations

# Хардкод, а не константы из кода: миграция должна остаться воспроизводимой,
# даже если тексты потом поменяют. Номер объявления подставляется вместо
# «№___» в NotificationSerializer.get_template
NEW_MESSAGE_CODE = 'new_message'
NEW_MESSAGE_PART1 = 'Новое сообщение по объявлению №___.'
NEW_MESSAGE_PART2 = 'Откройте чат, чтобы прочитать.'


def create_new_message_template(apps, schema_editor):
    """Заводит шаблон уведомления о новом сообщении.

    При деплое выполняется только migrate, фикстуры не загружаются, —
    поэтому шаблон приезжает миграцией, иначе уведомление не создастся.
    """
    NotificationTemplate = apps.get_model('notifications', 'NotificationTemplate')

    NotificationTemplate.objects.get_or_create(
        code=NEW_MESSAGE_CODE,
        defaults={'part1': NEW_MESSAGE_PART1, 'part2': NEW_MESSAGE_PART2},
    )


def remove_new_message_template(apps, schema_editor):
    """Убирает шаблон, если по нему еще не создавали уведомлений."""
    NotificationTemplate = apps.get_model('notifications', 'NotificationTemplate')

    NotificationTemplate.objects.filter(
        code=NEW_MESSAGE_CODE, notifications__isnull=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('notifications', '0004_devicetoken'),
    ]

    operations = [
        migrations.RunPython(create_new_message_template, remove_new_message_template),
    ]
