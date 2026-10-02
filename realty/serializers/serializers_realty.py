import base64

from django.core.files.base import ContentFile
from django.db.models import Max
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

from config import constants
from notifications.utils import create_notification
from realty import models as realty_models
from realty_addresses import serializers as address_serializers
from realty_photos.models import RealtyPhoto
from realty_photos.serializers import RealtyPhotoSerializer
from realty_specificities import models as specificities_models
from realty_specificities import serializers as specif_serializers
from realty_values import models as values_models


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


class PhotoUploadField(serializers.ListField):
    """Фото: принимает и base64-строку, и id уже загруженного фото."""

    child = serializers.CharField()

    def to_internal_value(self, data):
        if not isinstance(data, list):
            raise serializers.ValidationError('Expected a list of images or IDs.')

        processed_data = []
        for item in data:
            if isinstance(item, str) and item.startswith('data:image'):
                try:
                    format, img_str = item.split(';base64,')
                    ext = format.split('/')[-1]
                    processed_data.append(
                        ContentFile(base64.b64decode(img_str), name='img.' + ext)
                    )
                except Exception as err:
                    raise serializers.ValidationError(
                        'Invalid base64 image format.'
                    ) from err
            elif isinstance(item, int):
                processed_data.append(item)
            else:
                raise serializers.ValidationError(
                    'Each item must be a base64 image string or an integer ID.'
                )
        return processed_data


class RealtyBaseSerializer(serializers.ModelSerializer):
    """Чтение объявления, базовые поля."""

    is_deleted = serializers.BooleanField(read_only=True)
    is_commercial = serializers.SerializerMethodField()
    commercial_type = serializers.CharField(read_only=True)

    realty_status = serializers.IntegerField(source='realty_status_id', read_only=True)
    realty_status_full = serializers.CharField(
        source='realty_status.status', read_only=True
    )

    trade_type = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(read_only=True)
    owner = SlugRelatedField(slug_field='first_name', read_only=True)
    realty_type = SlugRelatedField(
        slug_field='type', queryset=values_models.RealtyType.objects.all()
    )
    address = address_serializers.AddressReadSerializer()
    about_building = specif_serializers.AboutBuildingSerializer()
    about_apartment = specif_serializers.AboutApartmentSerializer()
    common_characteristics = specif_serializers.CommonCharacteristicsSerializer()
    owner_type = SlugRelatedField(
        slug_field='participant',
        queryset=values_models.TradeParticipant.objects.all(),
    )
    communication_method = SlugRelatedField(
        slug_field='method',
        queryset=values_models.CommunicationMethod.objects.all(),
    )
    photos = RealtyPhotoSerializer(many=True, source='realty_photos')
    sale = serializers.SerializerMethodField()
    rent = serializers.SerializerMethodField()
    warnings = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = realty_models.Realty
        exclude = ['changed_at']

    def get_is_commercial(self, obj):
        return obj.realty_type.is_commercial

    def get_warnings(self, obj):
        if hasattr(obj, '_warnings'):
            return obj._warnings
        return self.context.get('warnings', [])

    def get_trade_type(self, obj):
        if hasattr(obj, 'sale_profile'):
            return 'sale'
        if hasattr(obj, 'rent_profile'):
            return 'rent'
        return 'unknown'

    def get_sale(self, obj):
        """Параметры продажи."""
        if hasattr(obj, 'sale_profile'):
            sale_profile = obj.sale_profile
            return {
                'id': sale_profile.id,
                'sales_parameters': specif_serializers.SalesParametersSerializer(
                    obj.sale_profile.sales_parameters
                ).data,
            }
        return None

    def get_rent(self, obj):
        """Условия аренды."""
        if hasattr(obj, 'rent_profile'):
            rent_profile = obj.rent_profile
            return {
                'id': rent_profile.id,
                'rental_features': specif_serializers.RentalFeaturesSerializer(
                    obj.rent_profile.rental_features
                ).data,
                'lease_payments': specif_serializers.LeasePaymentsSerializer(
                    obj.rent_profile.lease_payments
                ).data,
            }
        return None


class RealtyCreateSerializer(serializers.ModelSerializer):
    """Создание объявления."""

    is_deleted = serializers.BooleanField(read_only=True)

    owner = SlugRelatedField(slug_field='email', read_only=True)
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
    about_building = specif_serializers.AboutBuildingCreateSerializer(required=False)
    about_apartment = specif_serializers.AboutApartmentCreateSerializer(required=True)
    common_characteristics = specif_serializers.CommonCharacteristicsCreateSerializer(
        required=False
    )
    price = serializers.IntegerField(
        required=True,
    )
    commission = serializers.IntegerField(
        required=False,
        allow_null=True,
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
        required=False,
        write_only=True,
        help_text='Старое поле: Список новых фотографий в формате base64',
    )
    uploaded_photos_to_remove = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        help_text='Старое поле: Список ID фотографий, которые нужно удалить',
    )
    photos_upload = PhotoUploadField(
        required=False,
        write_only=True,
        help_text='Новое поле: Список новых фотографий (base64) или ID существующих для'
        ' '
        'обновления/сортировки',
    )
    warnings = serializers.SerializerMethodField(read_only=True)

    commercial_type = serializers.ChoiceField(
        choices=realty_models.Realty.COMMERCIAL_TYPE_CHOICES,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = realty_models.Realty
        fields = [
            'id',
            'is_deleted',
            'owner',
            'realty_type',
            'address',
            'about_building',
            'about_apartment',
            'common_characteristics',
            'description',
            'price',
            'commission',
            'owner_type',
            'communication_method',
            'uploaded_photos',
            'uploaded_photos_to_remove',
            'photos_upload',
            'warnings',
            'commercial_type',
        ]

    def get_warnings(self, obj):
        if hasattr(obj, '_warnings'):
            return obj._warnings
        return self.context.get('warnings', [])

    def validate_price(self, price):
        if price < constants.MIN_PRICE:
            raise serializers.ValidationError('Цена должна быть больше 0!')

        return price

    def validate_photos_upload(self, value):
        if self.instance:
            realty_instance = (
                self.instance.realty
                if hasattr(self.instance, 'realty')
                else self.instance
            )
            existing_photo_ids = set(
                realty_instance.realty_photos.values_list('id', flat=True)
            )

            for item in value:
                if isinstance(item, int) and item not in existing_photo_ids:
                    raise serializers.ValidationError(
                        f'Photo with ID {item} does not belong to this realty.'
                    )

        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                'Duplicate photo IDs are not allowed in the upload list.'
            )

        num_photos = len(value)

        if not (
            constants.NUMBER_OF_PHOTOS_MIN
            <= num_photos
            <= constants.NUMBER_OF_PHOTOS_MAX
        ):
            raise serializers.ValidationError(
                f'The number of photos must be between '
                f'{constants.NUMBER_OF_PHOTOS_MIN} and '
                f'{constants.NUMBER_OF_PHOTOS_MAX}.'
            )

        return value

    def _resolve(self, data, field):
        """Значение поля с учётом частичного обновления: из запроса или из объекта."""
        if field in data:
            return data[field]
        return getattr(self.instance, field, None)

    def _validate_commercial_type(self, data):
        """Тип коммерции обязателен для коммерческой и запрещён для жилой."""
        realty_type = self._resolve(data, 'realty_type')
        commercial_type = self._resolve(data, 'commercial_type')

        if realty_type is None:
            return

        if realty_type.is_commercial and not commercial_type:
            allowed = ', '.join(
                code for code, _ in realty_models.Realty.COMMERCIAL_TYPE_CHOICES
            )
            raise serializers.ValidationError(
                {
                    'commercial_type': (
                        f'Обязательно для коммерческой недвижимости. '
                        f'Допустимые значения: {allowed}.'
                    )
                }
            )

        if not realty_type.is_commercial and commercial_type:
            raise serializers.ValidationError(
                {
                    'commercial_type': (
                        'Указывается только для коммерческой недвижимости, '
                        f'а «{realty_type.type}» — жилая.'
                    )
                }
            )

    def validate(self, data):
        self._validate_commercial_type(data)

        warnings = []

        if data.get('photos_upload') and (
            data.get('uploaded_photos') or data.get('uploaded_photos_to_remove')
        ):
            warnings.append(
                'Поле photos_upload было использовано, поля uploaded_photos и '
                'uploaded_photos_to_remove будут проигнорированы.'
            )
            data.pop('uploaded_photos', None)
            data.pop('uploaded_photos_to_remove', None)
        elif not data.get('photos_upload') and (
            data.get('uploaded_photos') or data.get('uploaded_photos_to_remove')
        ):
            warnings.append(
                'Поля uploaded_photos и uploaded_photos_to_remove устарели и будут '
                'удалены в будущих версиях.'
            )

        self.context['warnings'] = warnings
        if self.instance:
            self.instance._warnings = warnings
        return data

    def create(self, validated_data):
        return self._create_realty(validated_data)

    def _create_realty(self, validated_data):
        address_data = validated_data.pop('address', None)
        about_building_data = validated_data.pop('about_building', None)
        about_apartment_data = validated_data.pop('about_apartment', None)
        common_characteristics_data = validated_data.pop('common_characteristics', None)
        uploaded_photos = validated_data.pop('uploaded_photos', None)
        _uploaded_photos_to_remove = validated_data.pop('uploaded_photos_to_remove', [])
        photos_upload = validated_data.pop('photos_upload', None)

        if address_data:
            address_serializer = address_serializers.AddressCreateSerializer(
                data=address_data
            )
            if 'street' in address_data:
                street_data = address_data['street']
                if 'city' in street_data:
                    city = street_data['city']
                    street_data['city'] = city.id
                if 'zone' in street_data and street_data['zone'] is not None:
                    zone = street_data['zone']
                    street_data['zone'] = zone.id
                if 'district' in street_data and street_data['district'] is not None:
                    district = street_data['district']
                    street_data['district'] = district.id

            if 'metro' in address_data and address_data['metro'] is not None:
                metro = address_data['metro']
                address_data['metro'] = metro.id

            address_serializer.is_valid(raise_exception=True)
            address = address_serializer.save()
            validated_data['address'] = address

        about_building = (
            specificities_models.AboutBuilding.objects.create(**about_building_data)
            if about_building_data
            else None
        )
        validated_data['about_building'] = about_building

        about_apartment = (
            specificities_models.AboutApartment.objects.create(**about_apartment_data)
            if about_apartment_data
            else None
        )
        validated_data['about_apartment'] = about_apartment

        common_characteristics = (
            specificities_models.CommonCharacteristics.objects.create(
                **common_characteristics_data
            )
            if common_characteristics_data
            else None
        )
        validated_data['common_characteristics'] = common_characteristics

        if 'realty_status' not in validated_data:
            default_status, _ = values_models.RealtyAdvStatus.objects.get_or_create(
                status=constants.REALTY_STATUS
            )
            validated_data['realty_status'] = default_status

        realty = realty_models.Realty.objects.create(**validated_data)

        if photos_upload:
            for sorter, photo_data in enumerate(photos_upload, 1):
                if isinstance(photo_data, ContentFile):
                    RealtyPhoto.objects.create(
                        realty=realty, image=photo_data, sorter=sorter
                    )
        elif uploaded_photos:
            for sorter, photo in enumerate(uploaded_photos, 1):
                RealtyPhoto.objects.create(realty=realty, image=photo, sorter=sorter)

        realty._warnings = self.context.get('warnings', [])

        if realty.realty_status.status == constants.REALTY_STATUS:
            create_notification(realty, 'on_moderation')
        return realty

    def update(self, instance, validated_data):
        return self._update_realty(instance, validated_data)

    def _update_realty(self, instance, validated_data):
        realty_instance = instance.realty if hasattr(instance, 'realty') else instance
        address_data = validated_data.pop('address', None)
        about_building_data = validated_data.pop('about_building', None)
        about_apartment_data = validated_data.pop('about_apartment', None)
        common_characteristics_data = validated_data.pop('common_characteristics', None)

        photos_upload = validated_data.pop('photos_upload', None)
        uploaded_photos = validated_data.pop('uploaded_photos', None)
        uploaded_photos_to_remove = validated_data.pop('uploaded_photos_to_remove', [])

        if address_data:
            if 'street' in address_data:
                street_data = address_data.pop('street', None)

                if 'city' in street_data:
                    city = street_data['city']
                    street_data['city'] = city.id

                if 'zone' in street_data and street_data['zone'] is not None:
                    zone = street_data['zone']
                    street_data['zone'] = zone.id
                else:
                    street_data['zone'] = None

                if 'district' in street_data and street_data['district'] is not None:
                    district = street_data['district']
                    street_data['district'] = district.id
                else:
                    street_data['district'] = None

                street_serializer = address_serializers.StreetCreateSerializer(
                    instance=realty_instance.address.street,
                    data=street_data,
                    partial=True,
                )
                street_serializer.is_valid(raise_exception=True)
                street_serializer.save()

            if 'metro' in address_data and address_data['metro'] is not None:
                metro = address_data['metro']
                address_data['metro'] = metro.id
            else:
                address_data['metro'] = None

            address_date_serializer = address_serializers.AddressCreateSerializer(
                instance=realty_instance.address, data=address_data, partial=True
            )
            address_date_serializer.is_valid(raise_exception=True)
            address_date_serializer.save()

        if about_building_data:
            if 'type' in about_building_data:
                type = about_building_data['type']
                about_building_data['type'] = type.id

            about_building_serializer = (
                specif_serializers.AboutBuildingCreateSerializer(
                    instance=realty_instance.about_building,
                    data=about_building_data,
                    partial=True,
                )
            )
            about_building_serializer.is_valid(raise_exception=True)
            about_building_serializer.save()

        if about_apartment_data:
            if 'number_of_rooms' in about_apartment_data:
                number_of_rooms = about_apartment_data['number_of_rooms']
                about_apartment_data['number_of_rooms'] = number_of_rooms.id

            about_apartment_serializer = (
                specif_serializers.AboutApartmentCreateSerializer(
                    instance=realty_instance.about_apartment,
                    data=about_apartment_data,
                    partial=True,
                )
            )
            about_apartment_serializer.is_valid(raise_exception=True)
            about_apartment_serializer.save()

        if common_characteristics_data:
            if 'repair_type' in common_characteristics_data:
                repair_type = common_characteristics_data['repair_type']
                common_characteristics_data['repair_type'] = repair_type.id

            if 'bathroom' in common_characteristics_data:
                bathroom = common_characteristics_data['bathroom']
                common_characteristics_data['bathroom'] = bathroom.id

            common_characteristics_serializer = (
                specif_serializers.CommonCharacteristicsCreateSerializer(
                    instance=realty_instance.common_characteristics,
                    data=common_characteristics_data,
                    partial=True,
                )
            )
            common_characteristics_serializer.is_valid(raise_exception=True)
            common_characteristics_serializer.save()

        if photos_upload is not None:
            current_photos = {
                photo.id: photo for photo in realty_instance.realty_photos.all()
            }
            photos_to_keep_ids = []
            new_photos_data = []

            for item in photos_upload:
                if isinstance(item, int):
                    photos_to_keep_ids.append(item)
                elif isinstance(item, ContentFile):
                    new_photos_data.append(item)

            for photo_id, photo_obj in current_photos.items():
                if photo_id not in photos_to_keep_ids:
                    photo_obj.delete()

            all_photos_in_order = []
            sorter = 1
            for item in photos_upload:
                if isinstance(item, int):
                    photo_obj = current_photos.get(item)
                    if photo_obj:
                        photo_obj.sorter = sorter
                        photo_obj.save()
                        all_photos_in_order.append(photo_obj)
                elif isinstance(item, ContentFile):
                    new_photo = RealtyPhoto.objects.create(
                        realty=realty_instance, image=item, sorter=sorter
                    )
                    all_photos_in_order.append(new_photo)
                sorter += 1
        else:
            if uploaded_photos_to_remove:
                realty_instance.realty_photos.filter(
                    id__in=uploaded_photos_to_remove
                ).delete()

            if uploaded_photos:
                max_sorter = realty_instance.realty_photos.aggregate(Max('sorter'))[
                    'sorter__max'
                ]
                next_sorter = (max_sorter or 0) + 1
                for photo in uploaded_photos:
                    RealtyPhoto.objects.create(
                        realty=realty_instance, image=photo, sorter=next_sorter
                    )
                    next_sorter += 1

        realty_instance._warnings = self.context.get('warnings', [])

        return super().update(realty_instance, validated_data)


class ShortRealtySerializer(serializers.ModelSerializer):
    """Короткая карточка объявления."""

    photos = RealtyPhotoSerializer(many=True, source='realty_photos')
    number_of_rooms = serializers.CharField(
        source='about_apartment.number_of_rooms.number_of_rooms'
    )
    realty_type = serializers.ReadOnlyField(source='realty_type.type')
    area = serializers.DecimalField(
        source='about_apartment.area', max_digits=10, decimal_places=2
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
        slug_field='method',
        queryset=values_models.CommunicationMethod.objects.all(),
    )
    floors_number = serializers.SerializerMethodField()
    rent = serializers.SerializerMethodField()

    realty_status = serializers.IntegerField(source='realty_status_id', read_only=True)
    realty_status_full = serializers.CharField(
        source='realty_status.status', read_only=True
    )

    # ========== ДЛЯ КОММЕРЧЕСКОЙ НЕДВИЖИМОСТИ ==========
    is_commercial = serializers.SerializerMethodField()
    commercial_type = serializers.CharField(read_only=True)

    def get_is_commercial(self, obj):
        return obj.realty_type.is_commercial

    class Meta:
        model = realty_models.Realty
        fields = (
            'id',
            'realty_status',
            'realty_status_full',
            'is_deleted',
            'photos',
            'price',
            'is_commercial',
            'commercial_type',
            'number_of_rooms',
            'realty_type',
            'area',
            'street',
            'house_number',
            'corpus',
            'building',
            'ownership',
            'metro',
            'metro_color',
            'owner_id',
            'owner_name',
            'owner_type',
            'communication_method',
            'floors_number',
            'published_at',
            'commission',
            'rent',
            'is_commercial',
            'commercial_type',
        )

    def get_floors_number(self, obj) -> str:
        return f'{obj.about_apartment.floor}/{obj.about_apartment.floors_number} этаж'

    def get_rent(self, obj):
        """Условия аренды."""
        if hasattr(obj, 'rent_profile'):
            return {
                'lease_payments': specif_serializers.LeasePaymentsSerializer(
                    obj.rent_profile.lease_payments
                ).data
            }
        return None


class RealtyPublicSerializer(ShortRealtySerializer):
    """Realty list serializer for anonymous users — минимальный набор полей."""

    class Meta(ShortRealtySerializer.Meta):
        fields = (
            'id',
            'realty_status',
            'realty_status_full',
            'photos',
            'price',
            'is_commercial',
            'commercial_type',
            'number_of_rooms',
            'realty_type',
            'area',
            'street',
            'house_number',
            'metro',
            'metro_color',
            'floors_number',
            'published_at',
            'rent',
        )
