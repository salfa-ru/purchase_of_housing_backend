from rest_framework import serializers

from .models import Realty, Sale, Rent
from realty_photos.serializers import RealtyPhotoSerializer


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
    street = serializers.ReadOnlyField(source='address.street.name')
    house_number = serializers.ReadOnlyField(source='address.house_number')
    corpus = serializers.ReadOnlyField(source='address.corpus')
    building = serializers.ReadOnlyField(source='address.building')
    ownership = serializers.ReadOnlyField(source='address.ownership')
    metro = serializers.ReadOnlyField(source='address.metro.name')

    class Meta:
        model = Realty
        fields = ("id",
                  "photos",
                  "price",
                  "number_of_rooms",
                  "realty_type",
                  "area",
                  "street",
                  "house_number",
                  "corpus",
                  "building",
                  "ownership",
                  "metro")


class SaleSerializer(serializers.ModelSerializer):
    realty = RealtySerializer()

    class Meta:
        model = Sale
        fields = ("realty",)


class RentSerializer(serializers.ModelSerializer):
    realty = RealtySerializer()

    class Meta:
        model = Rent
        fields = ("realty",)
