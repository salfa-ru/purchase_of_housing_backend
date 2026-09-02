from django.urls import path

from .views import (
    FavoriteCreateView,
    FavoriteDeleteView,
    FavoriteListCreateView,
    FavoriteMarkViewedView,
)

app_name = 'favorites'

urlpatterns = [
    path('', FavoriteListCreateView.as_view(), name='favorite-list'),
    path('create/', FavoriteCreateView.as_view(), name='favorite-create'),
    path('viewed/', FavoriteMarkViewedView.as_view(), name='favorite-viewed'),
    path('<int:pk>/', FavoriteDeleteView.as_view(), name='favorite-delete'),
]
