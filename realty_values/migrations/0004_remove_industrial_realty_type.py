from django.db import migrations

INDUSTRIAL_TYPE = 'Производственное помещение'


def remove_industrial_type(apps, schema_editor):
    """Производственного помещения нет в ТЗ. Убираем, пока оно свободно:
    тип с объявлениями удалять нельзя."""
    RealtyType = apps.get_model('realty_values', 'RealtyType')
    RealtyType.objects.filter(type=INDUSTRIAL_TYPE, realty__isnull=True).delete()


def restore_industrial_type(apps, schema_editor):
    """Возврат типа, если понадобится откатиться."""
    RealtyType = apps.get_model('realty_values', 'RealtyType')
    RealtyType.objects.get_or_create(
        type=INDUSTRIAL_TYPE, defaults={'is_commercial': True}
    )


class Migration(migrations.Migration):
    dependencies = [
        ('realty_values', '0003_commercial_realty_types'),
    ]

    operations = [
        migrations.RunPython(remove_industrial_type, restore_industrial_type),
    ]
