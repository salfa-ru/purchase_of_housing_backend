from rest_framework import serializers

from complaints.models import Complaint


class ComplaintsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['realty_id', 'description']