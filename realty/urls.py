from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import LatestRealtyViewSet

app_name = 'realty'


router_v1 = DefaultRouter()

router_v1.register(r'latest-realty', LatestRealtyViewSet,
                   basename='latest-realty')

urlpatterns = [
    path('', include(router_v1.urls)),
]
