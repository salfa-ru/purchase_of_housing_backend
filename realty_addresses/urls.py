from django.urls import path

from realty_addresses.apps import RealtyAddressesConfig
from realty_addresses.views import AddressMapPointsListAPIView

app_name = RealtyAddressesConfig.name

urlpatterns = [
    path('map-points/', AddressMapPointsListAPIView.as_view(), name='map-points')
]