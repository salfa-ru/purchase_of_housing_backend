from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для list, create, delete"""
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'user_type',
            'avatar',
            'uuid_esa',
            'updated_at',
            'date_joined',
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'username': {'read_only': True},
            'user_type': {'read_only': True},
            'avatar': {'read_only': True},
            'uuid_esa': {'read_only': True},
            'updated_at': {'read_only': True},
            'date_joined': {'read_only': True},
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        """При создании определяем username (нет в форме в дизайне), хэшируем пароль"""
        validated_data['username'] = validated_data['email']
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    def update(self, instance, validated_data):
        """При обновлении определяем username (нет в форме в дизайне), хэшируем пароль"""
        if validated_data.get('email'):
            validated_data['username'] = validated_data['email']
        user = super().update(instance, validated_data)
        if validated_data.get('password'):
            user.set_password(validated_data['password'])
            user.save()
        return user

