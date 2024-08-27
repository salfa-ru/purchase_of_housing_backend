from rest_framework.routers import DefaultRouter
from django.urls import include, path

from chats import views
from realty_addresses import views as address_viewsets


app_name = "address"

router = DefaultRouter()
router.register("address", address_viewsets.TestViewSet, basename="streets")


urlpatterns = [
    path("", include(router.urls)),
]
