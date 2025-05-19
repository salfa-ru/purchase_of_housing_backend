# realty/serializers/serializers_realty.py

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

import base64

from config import constants
from notifications.utils import create_notification
from realty import models as realty_models
from realty_photos.models import RealtyPhoto
from realty_values import models as values_models
from realty_specificities import models as specificities_models
from realty_addresses import serializers as address_serializers
from realty_specificities import serializers as specif_serializers
from realty_photos.serializers import RealtyPhotoSerializer


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            return self._decode_image(data)
        else:
            raise serializers.ValidationError('invalid image data')

    def _decode_image(self, data):
        format, img = data.split(';base64,')
        ext = format.split('/')[-1]
        return ContentFile(base64.b64decode(img), name='img.' + ext)


class RealtyBaseSerializer(serializers.ModelSerializer):
    """Realty Base Read Serializer."""

    is_deleted = serializers.BooleanField(read_only=True)   # <-- YYY --- realty_удаление v1

    realty_status = serializers.IntegerField(source='realty_status_id', read_only=True)
    realty_status_full = serializers.CharField(source='realty_status.status', read_only=True)

    trade_type = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(read_only=True)
    owner = SlugRelatedField(slug_field="first_name", read_only=True)
    realty_type = SlugRelatedField(
        slug_field="type", queryset=values_models.RealtyType.objects.all()
    )
    address = address_serializers.AddressReadSerializer()
    about_building = specif_serializers.AboutBuildingSerializer()
    about_apartment = specif_serializers.AboutApartmentSerializer()
    common_characteristics = (
        specif_serializers.CommonCharacteristicsSerializer()
    )
    owner_type = SlugRelatedField(
        slug_field="participant",
        queryset=values_models.TradeParticipant.objects.all(),
    )
    communication_method = SlugRelatedField(
        slug_field="method",
        queryset=values_models.CommunicationMethod.objects.all(),
    )
    photos = RealtyPhotoSerializer(
        many=True, source="realty_photos"
    )
    sale = serializers.SerializerMethodField()
    rent = serializers.SerializerMethodField()

    class Meta:
        model = realty_models.Realty
        exclude = ["changed_at"]

    def get_trade_type(self, obj):
        if hasattr(obj, "sale_profile"):
            return "sale"
        if hasattr(obj, "rent_profile"):
            return "rent"
        return "unknown"

    def get_sale(self, obj):
        """Return sales parameters."""
        if hasattr(obj, 'sale_profile'):
            sale_profile = obj.sale_profile
            return {
                "id": sale_profile.id,
                "sales_parameters": specif_serializers.SalesParametersSerializer(
                    obj.sale_profile.sales_parameters
                ).data
            }
        return None

    def get_rent(self, obj):
        """Return rental_features."""
        if hasattr(obj, 'rent_profile'):
            rent_profile = obj.rent_profile
            return {
                "id": rent_profile.id,
                "rental_features": specif_serializers.RentalFeaturesSerializer(
                    obj.rent_profile.rental_features
                ).data,
                "lease_payments": specif_serializers.LeasePaymentsSerializer(
                    obj.rent_profile.lease_payments
                ).data
            }
        return None


class RealtyCreateSerializer(serializers.ModelSerializer):
    """Realty Create Serializer."""

    is_deleted = serializers.BooleanField(read_only=True)   # <-- YYY --- realty_удаление v1

    owner = SlugRelatedField(slug_field="email", read_only=True)
    realty_type = serializers.PrimaryKeyRelatedField(
        queryset=values_models.RealtyType.objects.all(),
        required=True,
    )
    description = serializers.CharField(
        max_length=constants.DESCRIPTION_LENGTH,
        required=True,
    )
    address = address_serializers.AddressCreateSerializer(
        required=True,
    )
    about_building = specif_serializers.AboutBuildingCreateSerializer(
        required=False
    )
    about_apartment = specif_serializers.AboutApartmentCreateSerializer(
        required=True
    )
    common_characteristics = (
        specif_serializers.CommonCharacteristicsCreateSerializer(
            required=False
        )
    )
    price = serializers.IntegerField(
        required=True,
    )
    commission = serializers.IntegerField(
        required=False, allow_null=True,
    )
    owner_type = serializers.PrimaryKeyRelatedField(
        queryset=values_models.TradeParticipant.objects.all(),
        required=True,
    )
    communication_method = serializers.PrimaryKeyRelatedField(
        queryset=values_models.CommunicationMethod.objects.all(),
        required=True,
    )
    uploaded_photos = serializers.ListSerializer(
        child=Base64ImageField(),
    )
    uploaded_photos_to_remove = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,  # Поле только для записи
        help_text="Список ID фотографий, которые нужно удалить"
    )

    class Meta:
        model = realty_models.Realty
        fields = [
            "id",
            "is_deleted",
            "owner",
            "realty_type",
            "address",
            "about_building",
            "about_apartment",
            "common_characteristics",
            "description",
            "price",
            "commission",
            "owner_type",
            "communication_method",
            "uploaded_photos",
            "uploaded_photos_to_remove",
        ]

    def validate_price(self, price):
        if price < constants.MIN_PRICE:
            raise serializers.ValidationError(
                "Цена должна быть больше 0!"
            )

        return price

    # TODO validate_uploaded_photos_to_remove

    # def validate_uploaded_photos_to_remove(self, uploaded_photos_to_remove):
    #     if not self.instance:
    #         raise ValidationError("Объект не существует для проверки связанных фотографий.")
    #     existing_photo_ids = set(self.instance.realty_photos.values_list('id', flat=True))
    #     invalid_photo_ids = [photo_id for photo_id in uploaded_photos_to_remove if photo_id not in existing_photo_ids]

    #     if invalid_photo_ids:
    #         raise ValidationError(
    #             f"Следующие фотографии не связаны с этим объявлением: {', '.join(map(str, invalid_photo_ids))}"
    #         )
    #     return uploaded_photos_to_remove

    def create(self, validated_data):
        return self._create_realty(validated_data)

    def _create_realty(self, validated_data):
        address_data = validated_data.pop("address", None)
        about_building_data = validated_data.pop("about_building", None)
        about_apartment_data = validated_data.pop("about_apartment", None)
        common_characteristics_data = validated_data.pop(
            "common_characteristics", None
        )
        uploaded_photos = validated_data.pop("uploaded_photos", None)

        if address_data:
            address_serializer = address_serializers.AddressCreateSerializer(
                data=address_data
            )
            if "street" in address_data:
                street_data = address_data["street"]
                if "city" in street_data:
                    city = street_data["city"]
                    street_data["city"] = city.id
                if "zone" in street_data and street_data["zone"] is not None:
                    zone = street_data["zone"]
                    street_data["zone"] = zone.id
                if "district" in street_data and street_data["district"] is not None:
                    district = street_data["district"]
                    street_data["district"] = district.id

            if "metro" in address_data and address_data["metro"] is not None:
                metro = address_data["metro"]
                address_data["metro"] = metro.id

            address_serializer.is_valid(raise_exception=True)
            address = address_serializer.save()
            validated_data["address"] = address

        about_building = (specificities_models.AboutBuilding.objects.create(
            **about_building_data) if about_building_data else None)
        validated_data["about_building"] = about_building

        about_apartment = (specificities_models.AboutApartment.objects.create(
            **about_apartment_data) if about_apartment_data else None)
        validated_data["about_apartment"] = about_apartment

        common_characteristics = (specificities_models.CommonCharacteristics.objects.create(
            **common_characteristics_data) if common_characteristics_data else None)
        validated_data["common_characteristics"] = common_characteristics

        if "realty_status" not in validated_data:
            default_status, _ = (
                values_models.RealtyAdvStatus.objects.get_or_create(
                    status=constants.REALTY_STATUS
                )
            )
            validated_data["realty_status"] = default_status

        realty = realty_models.Realty.objects.create(**validated_data)

        if uploaded_photos:
            for photo in uploaded_photos:
                RealtyPhoto.objects.create(
                    realty=realty,
                    image=photo
                )

        # Отправка уведомления после успешного создания записи
        # Проверка статуса после создания записи, если запись на модерации - отправить уведомление.
        if realty.realty_status.status == constants.REALTY_STATUS:
            create_notification(realty, "on_moderation")
        return realty

    def update(self, instance, validated_data):
        return self._update_realty(instance, validated_data)

    def _update_realty(self, instance, validated_data):
        uploaded_photos_to_remove = validated_data.pop("uploaded_photos_to_remove", [])
        realty_instance = instance.realty if hasattr(instance, 'realty') else instance
        address_data = validated_data.pop("address", None)
        about_building_data = validated_data.pop("about_building", None)
        about_apartment_data = validated_data.pop("about_apartment", None)
        common_characteristics_data = validated_data.pop("common_characteristics", None)
        uploaded_photos = validated_data.pop("uploaded_photos", None)

        if address_data:
            if "street" in address_data:
                street_data = address_data.pop("street", None)

                if "city" in street_data:
                    city = street_data["city"]
                    street_data["city"] = city.id

                if "zone" in street_data and street_data["zone"] is not None:
                    zone = street_data["zone"]
                    street_data["zone"] = zone.id
                else:
                    street_data["zone"] = None

                if "district" in street_data and street_data["district"] is not None:
                    district = street_data["district"]
                    street_data["district"] = district.id
                else:
                    street_data["district"] = None

                street_serializer = address_serializers.StreetCreateSerializer(
                    instance=realty_instance.address.street,
                    data=street_data,
                    partial=True
                )
                street_serializer.is_valid(raise_exception=True)
                street_serializer.save()

            if "metro" in address_data and address_data["metro"] is not None:
                metro = address_data["metro"]
                address_data["metro"] = metro.id
            else:
                address_data["metro"] = None

            address_date_serializer = address_serializers.AddressCreateSerializer(
                instance=realty_instance.address,
                data=address_data,
                partial=True
            )
            address_date_serializer.is_valid(raise_exception=True)
            address_date_serializer.save()

        if about_building_data:
            if "type" in about_building_data:
                type = about_building_data["type"]
                about_building_data["type"] = type.id

            about_building_serializer = specif_serializers.AboutBuildingCreateSerializer(
                instance=realty_instance.about_building,
                data=about_building_data,
                partial=True
            )
            about_building_serializer.is_valid(raise_exception=True)
            about_building_serializer.save()

        if about_apartment_data:
            if "number_of_rooms" in about_apartment_data:
                number_of_rooms = about_apartment_data["number_of_rooms"]
                about_apartment_data["number_of_rooms"] = number_of_rooms.id

            about_apartment_serializer = specif_serializers.AboutApartmentCreateSerializer(
                instance=realty_instance.about_apartment,
                data=about_apartment_data,
                partial=True
            )
            about_apartment_serializer.is_valid(raise_exception=True)
            about_apartment_serializer.save()

        if common_characteristics_data:
            if "repair_type" in common_characteristics_data:
                repair_type = common_characteristics_data["repair_type"]
                common_characteristics_data["repair_type"] = repair_type.id

            if "bathroom" in common_characteristics_data:
                bathroom = common_characteristics_data["bathroom"]
                common_characteristics_data["bathroom"] = bathroom.id

            common_characteristics_serializer = specif_serializers.CommonCharacteristicsCreateSerializer(
                instance=realty_instance.common_characteristics,
                data=common_characteristics_data,
                partial=True
            )
            common_characteristics_serializer.is_valid(raise_exception=True)
            common_characteristics_serializer.save()

        if uploaded_photos_to_remove:
            realty_instance.realty_photos.filter(id__in=uploaded_photos_to_remove).delete()

        if uploaded_photos:
            for photo in uploaded_photos:
                RealtyPhoto.objects.create(realty=realty_instance, image=photo)

        return super().update(realty_instance, validated_data)


class ShortRealtySerializer(serializers.ModelSerializer):
    """Realty Short Detail Read Serializer."""

    photos = RealtyPhotoSerializer(
        many=True, source="realty_photos"
    )
    number_of_rooms = serializers.CharField(
        source="about_apartment.number_of_rooms.number_of_rooms"
    )
    realty_type = serializers.ReadOnlyField(source='realty_type.type')
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
    metro_color = serializers.ReadOnlyField(source='address.metro.line.color')
    owner_id = serializers.ReadOnlyField(source='owner.id')
    owner_name = serializers.ReadOnlyField(source='owner.first_name')
    owner_type = serializers.ReadOnlyField(source='owner_type.participant')
    communication_method = SlugRelatedField(
        slug_field="method",
        queryset=values_models.CommunicationMethod.objects.all(),
    )
    floors_number = serializers.SerializerMethodField()
    rent = serializers.SerializerMethodField()

    realty_status = serializers.IntegerField(source='realty_status_id', read_only=True)
    realty_status_full = serializers.CharField(source='realty_status.status', read_only=True)

    class Meta:
        model = realty_models.Realty
        fields = ("id",
                  'realty_status',
                  'realty_status_full',
                  "is_deleted",  # <-- YYY --- realty_удаление v1 ---- а почему нет в большом?
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
                  "metro",
                  "metro_color",
                  "owner_id",
                  "owner_name",
                  "owner_type",
                  "communication_method",
                  "floors_number",
                  "published_at",
                  "commission",
                  "rent",
                  )

    def get_floors_number(self, obj) -> str:
        return f"{obj.about_apartment.floor}/{obj.about_apartment.floors_number} этаж"

    def get_rent(self, obj):
        """Return rental_features."""
        if hasattr(obj, 'rent_profile'):
            return {
                "lease_payments": specif_serializers.LeasePaymentsSerializer(
                    obj.rent_profile.lease_payments
                ).data
            }
        return None
