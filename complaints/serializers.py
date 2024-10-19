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

    def validate(self, attrs):
        realty = attrs['realty']

        owner = self.context['request'].user

        if realty.owner == owner:
            raise serializers.ValidationError(
                'Вы не можете отправить жалобу на своё собственное объявление!'
            )

        return attrs
