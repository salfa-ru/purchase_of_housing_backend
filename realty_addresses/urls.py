from django.urls import path

from realty_addresses.apps import RealtyAddressesConfig
from realty_addresses.views import AddressMapPointListAPIView

app_name = RealtyAddressesConfig.name

urlpatterns = [
    path('map-points/', AddressMapPointListAPIView.as_view(), name='map-points')
]