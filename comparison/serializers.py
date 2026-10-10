from rest_framework import serializers

from realty.serializers.serializers_realty import RealtyBaseSerializer

from .models import Comparison


class ComparisonSerializer(serializers.ModelSerializer):
    """Объявление в сравнении вместе с характеристиками для таблицы."""

    realty = RealtyBaseSerializer(read_only=True, allow_null=True)
    realty_id = serializers.IntegerField()
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Comparison
        fields = ['id', 'realty_id', 'realty', 'is_available', 'added_at']
        read_only_fields = ['id', 'added_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_realty_deleted:
            data['realty'] = None
        return data


class ComparisonListSerializer(serializers.Serializer):
    """Ответ со списком сравнения."""

    count = serializers.IntegerField(read_only=True)
    max_count = serializers.IntegerField(read_only=True)
    results = ComparisonSerializer(many=True, read_only=True)
