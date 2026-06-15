"""
OtherCost API

GET    /api/other-costs/       — list all entries for current user
POST   /api/other-costs/       — add a new entry
DELETE /api/other-costs/<id>/  — delete an entry
"""

from rest_framework import generics, permissions
from .models import OtherCost
from .serializers import OtherCostSerializer


class OtherCostListCreateView(generics.ListCreateAPIView):
    serializer_class   = OtherCostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OtherCost.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OtherCostDestroyView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OtherCost.objects.filter(user=self.request.user)
