from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import viewsets

from realty import serializers as realty_serializers
from realty import models as realty_models


class BaseViewSet(viewsets.ModelViewSet):
    """Base viewset."""

    # filter_backends =
    http_method_names = ["post"]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class RealtyBaseViewSet(BaseViewSet):
    """Realty Base viewset.
    Viewing, creating, editing, removal."""

    queryset = realty_models.Realty.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return realty_serializers.RealtyCreateSerializer
        return realty_serializers.RealtyBaseSerializer


class SaleViewSet(BaseViewSet):
    """Sale Viewset."""

    queryset = realty_models.Sale.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return realty_serializers.SaleCreateSerializer
        #     elif self.action == "update" or self.action == "partial_update":
        #         return realty_serializers.SaleUpdateSerializer
        #     elif self.action == "destroy":
        #         return realty_serializers.SaleDeleteSerializer
        return realty_serializers.SaleReadSerializer


class RentViewSet(BaseViewSet):
    """Rent Viewset."""

    queryset = realty_models.Rent.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return realty_serializers.RentCreateSerializer
        #     elif self.action == "update" or self.action == "partial_update":
        #         return realty_serializers.RentUpdateSerializer
        #     elif self.action == "destroy":
        #         return realty_serializers.RentDeleteSerializer
        return realty_serializers.RentReadSerializer

    # на будущее для доб в избранное
    # @staticmethod
    # def create_obj(request, pk, serializers):
    #     user = request.user
    #     realty_data = {
    #         "owner": user.id,
    #         "realty_id": pk,
    #     }
    #     serializer = serializers(data=realty_data,
    # context={'request': request})
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)
