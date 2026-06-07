"""
Sales API

GET    /api/sales/         — list all sales for current user
POST   /api/sales/         — create a new sale with nested items
DELETE /api/sales/<id>/    — delete a sale (cascades to its items)
"""

from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Sale
from .serializers import SaleSerializer


class SaleListCreateView(generics.ListCreateAPIView):
    serializer_class   = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Sale.objects
            .filter(user=self.request.user)
            .prefetch_related("items")
            .order_by("-date", "-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SaleDestroyView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Sale.objects.filter(user=self.request.user)

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied
        return obj
