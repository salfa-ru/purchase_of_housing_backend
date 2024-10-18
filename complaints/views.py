from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from complaints.models import Complaint
from complaints.serializers import ComplaintsSerializer, ComplaintsListSerializer
from realty.models import Realty


@extend_schema(
    summary='Создание жалобы (передается в т.ч. id объявления, к которому жалоба '
            'и в поле description вводится текст жалобы)')
class ComplaintsCreateAPIView(generics.CreateAPIView):
    """Endpoint to Create complaints"""
    serializer_class = ComplaintsSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        owner = self.request.user

        serializer.save(owner=owner)


class ComplaintsListAPIView(generics.ListAPIView):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintsListSerializer
