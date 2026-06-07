"""
Purchases API

GET    /api/purchases/         — list all purchases for current user
POST   /api/purchases/         — create a new purchase
DELETE /api/purchases/<id>/    — delete a purchase
"""

from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Purchase
from .serializers import PurchaseSerializer


class PurchaseListCreateView(generics.ListCreateAPIView):
    serializer_class   = PurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Purchase.objects.filter(user=self.request.user).order_by("-date", "-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PurchaseDestroyView(generics.DestroyAPIView):
    serializer_class   = PurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Purchase.objects.filter(user=self.request.user)

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied
        return obj
