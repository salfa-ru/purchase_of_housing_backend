from rest_framework import generics

from complaints.serializers import ComplaintsSerializer
from realty.models import Realty


class ComplaintsCreateAPIView(generics.CreateAPIView):
    serializer_class = ComplaintsSerializer

    def perform_create(self, serializer):
        owner = self.request.user
        realty_id = self.request.data.get('realty_id')
        realty = Realty.objects.get(pk=realty_id)
        serializer.save(owner=owner, realty=realty)