from django.db import migrations

# Названия совпадают с подписями в Realty.COMMERCIAL_TYPE_CHOICES: справочник
# типов недвижимости и выбор типа коммерции должны говорить об одном и том же
COMMERCIAL_TYPES = [
    'Офис',
    'Торговое помещение',
    'Склад',
    'Помещение свободного назначения',
    'Производственное помещение',
]


def create_commercial_types(apps, schema_editor):
    """Заводит коммерческие типы. Без них модуль не может отдать ни одного объекта."""
    RealtyType = apps.get_model('realty_values', 'RealtyType')

    for name in COMMERCIAL_TYPES:
        realty_type, created = RealtyType.objects.get_or_create(
            type=name, defaults={'is_commercial': True}
        )
        # Тип мог быть заведён руками через админку и остаться жилым
        if not created and not realty_type.is_commercial:
            realty_type.is_commercial = True
            realty_type.save(update_fields=['is_commercial'])


def remove_commercial_types(apps, schema_editor):
    """Убирает только незанятые типы: удалить тип с объявлениями нельзя."""
    RealtyType = apps.get_model('realty_values', 'RealtyType')
    RealtyType.objects.filter(type__in=COMMERCIAL_TYPES, realty__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('realty_values', '0002_realtytype_is_commercial'),
        ('realty', '0003_realty_commercial_type'),
    ]

    operations = [
        migrations.RunPython(create_commercial_types, remove_commercial_types),
    ]
