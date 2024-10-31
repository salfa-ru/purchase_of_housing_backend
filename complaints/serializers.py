from rest_framework import serializers

from complaints.models import Complaint
from realty.models import Realty


class ComplaintsSerializer(serializers.ModelSerializer):
    realty_id = serializers.PrimaryKeyRelatedField(
        queryset=Realty.objects.all(),
        source='realty',
        write_only=True
    )

    class Meta:
        model = Complaint
        fields = ['realty_id', 'description']

    def validate_description(self, value):
        if not (50 <= len(value) <= 200):
            raise serializers.ValidationError('Описание должно содержать от 50 до 200 символов.')
        return value

    def validate(self, attrs):
        realty = attrs['realty']

        owner = self.context['request'].user

        if realty.owner == owner:
            raise serializers.ValidationError(
                'Вы не можете отправить жалобу на своё собственное объявление!'
            )

        elif realty.realty_status.status != "Активно":
            raise serializers.ValidationError("Вы не можете отправить жалобу если объявление не активно!")

        return attrs
