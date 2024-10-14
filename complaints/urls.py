from django.urls import path

from complaints.apps import ComplaintsConfig
from complaints.views import ComplaintsCreateAPIView

app_name = ComplaintsConfig.name

urlpatterns = [
    path('create/', ComplaintsCreateAPIView.as_view(), name='create-complaints')
]