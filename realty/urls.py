# from rest_framework.routers import DefaultRouter
from django.urls import path  # include

from .views import LastRentsView, LastSalesView, RealtyListView

app_name = 'realty'


# router = DefaultRouter()

# router.register(
#     r"realty-list", RealtyListView, basename="realty-list"
# )


urlpatterns = [
    # path("", include(router.urls)),
    path('latest-rent/', LastRentsView.as_view(), name='sale-list'),
    path('latest-sale/', LastSalesView.as_view(), name='latest-sale'),
    path('', RealtyListView.as_view(), name='realty-list'),
]
