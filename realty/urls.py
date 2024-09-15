from django.urls import path

from .views import RealtyListView, LastRealtyListView, RealtyDetailView

app_name = 'realty'

urlpatterns = [
    path('latest/', LastRealtyListView.as_view(), name='latest'),
    path('', RealtyListView.as_view(), name='realty-list'),
    path('<int:pk>/', RealtyDetailView.as_view(), name='realty-detail'),
]
