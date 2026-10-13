from rest_framework import serializers

from realty.serializers.serializers_realty import RealtyBaseSerializer

from .models import Comparison


class ComparisonSerializer(serializers.ModelSerializer):
    """Объявление в сравнении вместе с характеристиками для таблицы."""

    realty = RealtyBaseSerializer(read_only=True, allow_null=True)
    realty_id = serializers.IntegerField()
    trade_type = serializers.CharField(
        source='realty.trade_type',
        read_only=True,
        help_text='Список, в который попало объявление: sale или rent',
    )
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Comparison
        fields = ['id', 'realty_id', 'trade_type', 'realty', 'is_available', 'added_at']
        read_only_fields = ['id', 'added_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_realty_deleted:
            data['realty'] = None
        return data


class ComparisonTableSerializer(serializers.Serializer):
    """Один список сравнения: объявления одного типа сделки."""

    count = serializers.IntegerField(read_only=True)
    results = ComparisonSerializer(many=True, read_only=True)


class ComparisonListSerializer(serializers.Serializer):
    """Ответ со списками сравнения: отдельно продажа и аренда."""

    max_count = serializers.IntegerField(
        read_only=True, help_text='Сколько объявлений можно положить в один список'
    )
    sale = ComparisonTableSerializer(read_only=True, help_text='Список продажи')
    rent = ComparisonTableSerializer(read_only=True, help_text='Список аренды')
