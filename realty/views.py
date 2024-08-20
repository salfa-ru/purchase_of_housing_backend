from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from realty import serializers as realty_serializers
from realty import models as realty_models


from users.models import User


class RealtyBaseViewSet(viewsets.ModelViewSet):
    """Realty Base viewset.
    Viewing, creating, editing, removal."""

    queryset = realty_models.Realty.objects.all()
    # permission_classes =
    serializer_class = realty_serializers.RealtyBaseSerializer
    # filter_backends =

    # def perform_create(self, serializer):
    #     serializer.save(owner=self.request.user)


class SaleViewSet(RealtyBaseViewSet):
    """Sale Viewset."""

    queryset = realty_models.Sale.objects.all()
    serializer_class = realty_serializers.SaleReadSerializer


class RentViewSet(RealtyBaseViewSet):
    """Rent Viewset."""

    queryset = realty_models.Rent.objects.all()
    serializer_class = realty_serializers.RentReadSerializer

    # def get_serializer_class(self):
    #     if self.action == "create":
    #         return realty_serializers.RealtyCreateSerializer
    #     elif self.action == "update" or self.action == "partial_update":
    #         return realty_serializers.RealtyUpdateSerializer
    #     elif self.action == "destroy":
    #         return realty_serializers.RealtyDeleteSerializer
    #     return realty_serializers.RealtyReadSerializer

    # @staticmethod
    # def create_obj(request, pk, serializers): # на будущее для доб в избранное
    #     user = request.user
    #     realty_data = {
    #         "owner": user.id,
    #         "realty_id": pk,
    #     }
    #     serializer = serializers(data=realty_data, context={'request': request})
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)
