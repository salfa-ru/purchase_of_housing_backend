from rest_framework import serializers
from django.core.validators import FileExtensionValidator
from config import constants

from .models import RealtyPhoto


class RealtyPhotoSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(validators=[
            FileExtensionValidator(
                allowed_extensions=constants.IMAGE_EXTENSIONS)],
            )

    class Meta:
        model = RealtyPhoto
        fields = ("image",)
