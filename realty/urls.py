from django.urls import path

from .views import LastRentsView, LastSalesView, RealtyListView

app_name = 'realty'


urlpatterns = [
    path('latest-rent/', LastRentsView.as_view(), name='sale-list'),
    path('latest-sale/', LastSalesView.as_view(), name='latest-sale'),
    path('realty/', RealtyListView.as_view(), name='realty-list'),
]
