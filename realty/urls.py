# realty/urls.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CatalogRentCommercialView,
    CatalogRentResidentialView,
    CatalogSaleCommercialView,
    CatalogSaleResidentialView,
    ChangeStatusUpdateAPIView,
    LastRealtyListView,
    RealtyBatchView,
    RealtyCountView,
    RealtyDeleteView,
    RealtyDetailView,
    RealtyFilterOptionsView,
    RealtyListView,
    RealtyLKListView,
    RealtyOwnerContactsView,
    RealtyOwnerDataView,
    RentViewSet,
    SaleViewSet,
)

app_name = 'realty'

router = DefaultRouter()

router.register('sales', SaleViewSet, basename='sales')
router.register('rents', RentViewSet, basename='rents')

urlpatterns = [
    path('count/', RealtyCountView.as_view(), name='realty-count'),
    path('latest/', LastRealtyListView.as_view(), name='latest'),
    path('', RealtyListView.as_view(), name='realty-list'),
    path('my-realty/', RealtyLKListView.as_view(), name='my-realty'),
    path('<int:pk>/', RealtyDetailView.as_view(), name='realty-detail'),
    path('<int:pk>/owner/', RealtyOwnerDataView.as_view(), name='owner-data'),
    path(
        '<int:pk>/contacts/', RealtyOwnerContactsView.as_view(), name='owner-contacts'
    ),
    path('<int:pk>/status/', ChangeStatusUpdateAPIView.as_view(), name='change-status'),
    path('<int:pk>/delete/', RealtyDeleteView.as_view(), name='realty-delete'),
    path('', include(router.urls)),
    path('filter-options/', RealtyFilterOptionsView.as_view(), name='filter-options'),
    path('batch/', RealtyBatchView.as_view(), name='realty-batch'),
    # Каталоги недвижимости (4 типа)
    path(
        'catalog/sale/residential/',
        CatalogSaleResidentialView.as_view(),
        name='catalog-sale-residential',
    ),
    path(
        'catalog/sale/commercial/',
        CatalogSaleCommercialView.as_view(),
        name='catalog-sale-commercial',
    ),
    path(
        'catalog/rent/residential/',
        CatalogRentResidentialView.as_view(),
        name='catalog-rent-residential',
    ),
    path(
        'catalog/rent/commercial/',
        CatalogRentCommercialView.as_view(),
        name='catalog-rent-commercial',
    ),
]
