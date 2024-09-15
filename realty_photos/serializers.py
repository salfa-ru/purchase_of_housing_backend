from rest_framework import serializers

from .models import RealtyPhoto


class RealtyPhotoSerializer(serializers.ModelSerializer):

    class Meta:
        model = RealtyPhoto
        fields = ("image",)
