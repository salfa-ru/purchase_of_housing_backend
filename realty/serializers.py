from rest_framework import serializers

from .models import Realty
from realty_photos.serializers import RealtyPhotoSerializer
from realty_addresses.serializers import AddressSerializer


class RealtySerializer(serializers.ModelSerializer):
    photos = RealtyPhotoSerializer(
        many=True, source="realty_photos"
    )
    rooms = serializers.CharField(
        source="about_apartment.number_of_rooms.number_of_rooms"
    )
    area = serializers.DecimalField(
        source="about_apartment.area",
        max_digits=10, decimal_places=2
    )
    address = AddressSerializer()

    class Meta:
        model = Realty
        fields = ("id",
                  "photos",
                  "price",
                  "rooms",
                  "realty_type",
                  "area",
                  "address",
                  "metro")
