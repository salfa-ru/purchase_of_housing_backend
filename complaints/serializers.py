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


class ComplaintsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['is_new', 'description', 'owner']
