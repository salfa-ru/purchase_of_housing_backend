from rest_framework import serializers

from realty.serializers.serializers_realty import RealtyBaseSerializer

from .models import Favorite


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного"""

    realty = RealtyBaseSerializer(
        read_only=True
    )  # Вложенный объект недвижимости (как в GET /realty/{id}/)
    realty_id = serializers.IntegerField(
        write_only=True
    )  # Поле только для записи (фронт присылает ID)

    class Meta:
        model = Favorite
        fields = [
            'id',
            'realty',
            'realty_id',
            'added_at',
            'is_viewed',
        ]
        read_only_fields = [
            'id',
            'added_at',
        ]  # Поля, которые нельзя изменить через API


class FavoriteViewedSerializer(serializers.Serializer):
    """Ответ сброса счётчика непросмотренных."""

    status = serializers.CharField(read_only=True)
    update_count = serializers.IntegerField(read_only=True)
