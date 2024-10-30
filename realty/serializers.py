from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from config import constants
from notifications.utils import create_notification
from realty import models as realty_models
from .models import Realty, Sale, Rent
from realty_values import models as values_models
from realty_specificities import models as specificities_models
from realty_addresses import serializers as address_serializers
from realty_specificities import serializers as specif_serializers
from realty_displays import serializers as displays_serializers
from realty_photos.serializers import RealtyPhotoSerializer
from users.serializers import UserDataSerializer, UserContactsSerializer
from django.core.exceptions import ValidationError


class RealtyBaseSerializer(serializers.ModelSerializer):
    """Realty Base Read Serializer."""

    owner = SlugRelatedField(slug_field="username", read_only=True)  # или slug_field="email" ?
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
    sale = serializers.SerializerMethodField()
    rent = serializers.SerializerMethodField()

    class Meta:
        model = realty_models.Realty
        exclude = ["changed_at", "realty_status", ]

    def get_sale(self, obj):
        """Return sales parameters."""
        if hasattr(obj, 'sale_profile'):
            return {
                "sales_parameters": specif_serializers.SalesParametersSerializer(
                    obj.sale_profile.sales_parameters
                ).data
            }
        return None

    def get_rent(self, obj):
        """Return rental_features."""
        if hasattr(obj, 'rent_profile'):
            return {
                "rental_features": specif_serializers.RentalFeaturesSerializer(
                    obj.rent_profile.rental_features
                ).data,
                "lease_payments": specif_serializers.LeasePaymentsSerializer(
                    obj.rent_profile.lease_payments
                ).data
            }
        return None


class SaleReadSerializer(serializers.ModelSerializer):
    """Sale Read Serializer."""

    realty = RealtyBaseSerializer()
    sales_parameters = specif_serializers.SalesParametersSerializer()

    class Meta:
        model = realty_models.Sale
        fields = "__all__"


class RentReadSerializer(serializers.ModelSerializer):
    """Rent Read Serializer."""

    realty = RealtyBaseSerializer()
    rental_features = specif_serializers.RentalFeaturesSerilalizer()
    lease_payments = specif_serializers.LeasePaymentsSerializer()

    class Meta:
        model = realty_models.Rent
        fields = "__all__"


class RealtyCreateSerializer(serializers.ModelSerializer):
    """Realty Create Serializer."""

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
        required=False,
    )
    owner_type = serializers.PrimaryKeyRelatedField(
        queryset=values_models.TradeParticipant.objects.all(),
        required=True,
    )
    communication_method = serializers.PrimaryKeyRelatedField(
        queryset=values_models.CommunicationMethod.objects.all(),
        required=True,
    )

    class Meta:
        model = realty_models.Realty
        fields = [
            "id",
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
        ]

    def create(self, validated_data):
        return self._create_realty(validated_data)

    def _create_realty(self, validated_data):
        address_data = validated_data.pop("address", None)
        about_building_data = validated_data.pop("about_building", None)
        about_apartment_data = validated_data.pop("about_apartment", None)
        common_characteristics_data = validated_data.pop(
            "common_characteristics", None
        )

        if address_data:
            address_serializer = address_serializers.AddressCreateSerializer(
                data=address_data
            )
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

        # Отправка уведомления после успешного создания записи
        # Проверка статуса после создания записи, если запись на модерации - отправить уведомление.
        if realty.realty_status.status == constants.REALTY_STATUS:
            create_notification(realty, "on_moderation")

        return realty


class RentCreateSerializer(serializers.ModelSerializer):
    """Rent Create Serializer."""

    realty = RealtyCreateSerializer(required=True)
    rental_features = specif_serializers.RentalFeaturesSerilalizer(
        required=False
    )
    lease_payments = specif_serializers.LeasePaymentsCreateSerializer(
        required=False
    )

    def create(self, validated_data):
        realty_data = validated_data.pop("realty", None)
        rental_features_data = validated_data.pop("rental_features", None)
        lease_payments_data = validated_data.pop("lease_payments", None)

        if realty_data:
            realty_data["owner"] = self.context["request"].user
            realty = RealtyCreateSerializer(
                context=self.context
            )._create_realty(realty_data)
            validated_data["realty"] = realty

        rental_features = (specificities_models.RentalFeatures.objects.create(
            **rental_features_data) if rental_features_data else None)
        validated_data["rental_features"] = rental_features

        lease_payments = (specificities_models.LeasePayments.objects.create(
            **lease_payments_data) if lease_payments_data else None)
        validated_data["lease_payments"] = lease_payments
        validated_data.pop("owner", None)
        rent = realty_models.Rent.objects.create(**validated_data)
        return rent

    class Meta:
        model = realty_models.Rent
        fields = "__all__"


class SaleCreateSerializer(serializers.ModelSerializer):
    """Sale Create Serializer."""

    realty = RealtyCreateSerializer(required=True)

    class Meta:
        model = realty_models.Sale
        exclude = [
            "sales_parameters",
        ]

    def create(self, validated_data):
        realty_data = validated_data.pop("realty", None)

        if realty_data:
            realty_data["owner"] = self.context["request"].user
            realty = RealtyCreateSerializer(
                context=self.context
            )._create_realty(realty_data)
            validated_data["realty"] = realty

        if "sales_parameters" not in validated_data:
            housing_type, _ = values_models.HousingType.objects.get_or_create(
                type=constants.HOUSING_TYPE
            )
            sale_type, _ = values_models.SaleType.objects.get_or_create(
                type=constants.SALE_TYPE
            )
            sales_parameters, _ = (
                specificities_models.SalesParameters.objects.get_or_create(
                    housing_type=housing_type, sale_type=sale_type
                )
            )
            validated_data["sales_parameters"] = sales_parameters

        validated_data.pop("owner", None)
        sale = realty_models.Sale.objects.create(**validated_data)
        return sale


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


class ShortSaleSerializer(serializers.ModelSerializer):
    """Sale Short Detail Read Serializer."""

    realty = ShortRealtySerializer()

    class Meta:
        model = Sale
        fields = ("realty",)


class ShortRentSerializer(serializers.ModelSerializer):
    """Rent Short Detail Read Serializer."""

    realty = ShortRealtySerializer()

    class Meta:
        model = Rent
        fields = ("realty",)


class CountRealtySerializer(RealtyBaseSerializer):
    """Filtered Realty Count Serializer."""

    count = serializers.IntegerField()

    class Meta:
        model = realty_models.Realty
        fields = ('count',)


class RealtyOwnerDataSerializer(serializers.ModelSerializer):
    """Realty's Owner Contacts Serializer."""

    owner = UserDataSerializer(read_only=True)
    owner_type = serializers.ReadOnlyField(source='owner_type.participant')
    communication_method = serializers.CharField(
        source='communication_method.method', read_only=True)

    class Meta:
        model = Realty
        fields = ("owner",
                  "owner_type",
                  "communication_method",
                  )


class RealtyOwnerContactsSerializer(serializers.ModelSerializer):
    """Realty's Owner Contacts Serializer."""

    owner = UserContactsSerializer(read_only=True)
    owner_type = serializers.ReadOnlyField(source='owner_type.participant')

    class Meta:
        model = Realty
        fields = ("owner",
                  "owner_type",
                  )


class RealtyLKSerializer(serializers.Serializer):
    """Serializer for Realty objects with added view counts and status."""

    short_realty_data = ShortRealtySerializer()
    counter_views = displays_serializers.CounterViewsSerializer()
    realty_status = serializers.IntegerField(source='realty_status_id')

    def to_representation(self, instance):
        representation = {
            'short_realty_data': ShortRealtySerializer(instance).data,
            'realty_status': instance.realty_status_id
        }

        # статусы из realty_values_realtyadvstatus
        # 1 - Активно
        # 2 - На модерации
        # 3 - Отклонено
        # 4 - В архиве

        if instance.realty_status_id == 1:  # Выдавать ответ только если объявление Активно
            representation['counter_views'] = displays_serializers.CounterViewsSerializer(instance).data
        else:
            representation['counter_views'] = {}  # пустой ответ если объявление не активно

        return representation


class RealtyStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for update realty_status"""

    class Meta:
        model = Realty
        fields = ['realty_status']

    def validate_realty_status(self, value):

        obj = self.instance
        request = self.context.get('request')
        if obj.owner == request.user:
            allowed_transitions = {
                'Активно': ['В архиве'],
                'Отклонено': ['В архиве'],
                'На модерации': ['В архиве'],
                'В архиве': ['На модерации']
            }

            if obj.realty_status.status in allowed_transitions:

                if str(value) not in allowed_transitions[obj.realty_status.status]:
                    raise ValidationError(
                        f"Статус можно изменить с '{obj.realty_status.status}' "
                        f"только на {allowed_transitions[obj.realty_status.status]}."
                    )
            else:
                raise ValidationError(f"Недопустимая операция: статус '{obj.realty_status.status}' нельзя изменить.")

            return value
        else:
            raise ValidationError(f"Вы не являетесь владельцем объявления!")
