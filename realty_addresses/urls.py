from django.urls import path

from realty_addresses.apps import RealtyAddressesConfig
from realty_addresses.views import (
    GetListAnnouncementsInMapPoint,
    GetlistMapPointsAPIView,
    MetroStationsAPIView,
)

app_name = RealtyAddressesConfig.name

urlpatterns = [
    path('map-points/', GetlistMapPointsAPIView.as_view(), name='map-points'),
    path(
        'map-point-realty/',
        GetListAnnouncementsInMapPoint.as_view(),
        name='map-point-realty',
    ),
    path('metro/', MetroStationsAPIView.as_view(), name='metro-stations'),
]
