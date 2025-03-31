# realty/urls.py

from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views import (RealtyListView, LastRealtyListView, RealtyDetailView,
                    RealtyCountView, RealtyOwnerContactsView,
                    RealtyOwnerDataView, RealtyLKListView, SaleViewSet,
                    RentViewSet, ChangeStatusUpdateAPIView, RealtyFilterOptionsView)

app_name = "realty"

router = DefaultRouter()

router.register("sales", SaleViewSet, basename="sales")
router.register("rents", RentViewSet, basename="rents")

urlpatterns = [
    path('count/', RealtyCountView.as_view(), name='realty-count'),
    path('latest/', LastRealtyListView.as_view(), name='latest'),
    path('', RealtyListView.as_view(), name='realty-list'),
    path('my-realty/', RealtyLKListView.as_view(), name='my-realty'),
    path('<int:pk>/', RealtyDetailView.as_view(), name='realty-detail'),
    path('<int:pk>/owner/', RealtyOwnerDataView.as_view(), name='owner-data'),
    path('<int:pk>/contacts/', RealtyOwnerContactsView.as_view(), name='owner-contacts'),
    path('<int:pk>/status/', ChangeStatusUpdateAPIView.as_view(), name='change-status'),
    path("", include(router.urls)),
    path('filter-options/', RealtyFilterOptionsView.as_view(), name='filter-options')
]
