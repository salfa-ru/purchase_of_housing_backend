from rest_framework import serializers

from .models import Realty, Sale, Rent
from realty_photos.serializers import RealtyPhotoSerializer
from realty_addresses.serializers import AddressSerializer


class RealtySerializer(serializers.ModelSerializer):
    photos = RealtyPhotoSerializer(
        many=True, source="realty_photos"
    )
    number_of_rooms = serializers.CharField(
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
                  "number_of_rooms",
                  "realty_type",
                  "area",
                  "address",)
                #   "metro",)


class SaleSerializer(serializers.ModelSerializer):
    realty = RealtySerializer()

    class Meta:
        model = Sale
        fields = ("id",
                  "realty",)


class RentSerializer(serializers.ModelSerializer):
    realty = RealtySerializer()

    class Meta:
        model = Rent
        fields = ("id",
                  "realty")
