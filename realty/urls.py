from rest_framework.routers import DefaultRouter
from django.urls import include, path

from realty import views as realty_viewsets


app_name = "realty"

router = DefaultRouter()

router.register("sales", realty_viewsets.SaleViewSet, basename="sales")
router.register("rents", realty_viewsets.RentViewSet, basename="rents")


urlpatterns = [
    path("", include(router.urls)),
]
