from django.urls import path
from .views import FavoriteListView, FavoriteCreateView, FavoriteDeleteView, FavoriteMarkViewedView

app_name = 'favorites'

urlpatterns = [
    path('create/', FavoriteCreateView.as_view(), name='favorite-create'),
    path('', FavoriteListView.as_view(), name='favorite-list'),
    path('<int:pk>/', FavoriteDeleteView.as_view(), name='favorite-delete'),
    path('viewed/', FavoriteMarkViewedView.as_view(), name='favorite-viewed'),
]