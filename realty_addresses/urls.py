from django.urls import path

from realty_addresses.apps import RealtyAddressesConfig
from realty_addresses.views import GetlistMapPointsAPIView, GetListAnnouncementsInMapPoint

app_name = RealtyAddressesConfig.name

urlpatterns = [
    path('map-points/', GetlistMapPointsAPIView.as_view(), name='map-points'),
    path('map-point-realties/', GetListAnnouncementsInMapPoint.as_view(), name='map-point-realties')
]