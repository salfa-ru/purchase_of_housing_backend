from django.urls import path

from complaints.apps import ComplaintsConfig
from complaints.views import ComplaintsCreateAPIView, ComplaintsListAPIView

app_name = ComplaintsConfig.name

urlpatterns = [
    path('', ComplaintsCreateAPIView.as_view(), name='create-complaints'),
    path('get-complaints/', ComplaintsListAPIView.as_view(), name='list-complaints')
]