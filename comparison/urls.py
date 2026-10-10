from django.urls import path

from .views import ComparisonDeleteView, ComparisonListCreateView

app_name = 'comparison'

urlpatterns = [
    path('', ComparisonListCreateView.as_view(), name='comparison-list'),
    path('<int:realty_id>/', ComparisonDeleteView.as_view(), name='comparison-delete'),
]
