from rest_framework import serializers
from .models import Favorite
from realty.serializers.serializers_realty import RealtyBaseSerializer


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранного"""

    realty = RealtyBaseSerializer(read_only=True)  # Вложенный объект недвижимости (как в GET /realty/{id}/)
    realty_id = serializers.IntegerField(write_only=True)  # Поле только для записи (фронт присылает ID)

    class Meta:
        model = Favorite
        fields = [
            'id',
            'realty',
            'realty_id',
            'added_at',
            'is_viewed',
        ]
        realty_only_fields = ['id', 'added_at']  # Поля, которые нельзя изменить через API
