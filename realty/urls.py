from django.urls import path

from .views import (RealtyListView, LastRealtyListView, RealtyDetailView,
                    RealtyCountView, RealtyOwnerContactsView,
                    RealtyOwnerDataView)

app_name = 'realty'

urlpatterns = [
    path('count/', RealtyCountView.as_view(), name='realty-count'),
    path('latest/', LastRealtyListView.as_view(), name='latest'),
    path('', RealtyListView.as_view(), name='realty-list'),
    path('<int:pk>/', RealtyDetailView.as_view(), name='realty-detail'),
    path('<int:pk>/owner/', RealtyOwnerDataView.as_view(), name='owner-data'),
    path('<int:pk>/contacts/', RealtyOwnerContactsView.as_view(), name='owner-contacts'),
]
