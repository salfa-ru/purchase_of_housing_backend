from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import LastRentsView, LastSalesView  # LatestRealtyViewSet

app_name = 'realty'


router_v1 = DefaultRouter()

# router_v1.register(r'latest-realty', LatestRealtyViewSet,
#                   basename='latest-realty')
router_v1.register(r'latest-rent', LastRentsView, basename='latest-rent')
router_v1.register(r'latest-sale', LastSalesView, basename='latest-sale')

urlpatterns = [
    path('', include(router_v1.urls)),
]
