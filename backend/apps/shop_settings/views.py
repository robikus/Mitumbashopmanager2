"""
ShopSettings API — single object per user (get/update).

GET  /api/settings/   → return user's settings (creates defaults on first call)
PUT  /api/settings/   → update all settings fields + replace categories list
"""

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from .models import ShopSettings, ProductCategory
from .serializers import ShopSettingsSerializer

DEFAULT_CATEGORIES = [
    "Tops", "Dresses", "Belts", "Handbags", "Trousers",
    "Jackets", "Kids Clothes", "Shoes", "Skirts", "Accessories",
]


def get_or_create_settings(user):
    """Return the user's ShopSettings, creating it with defaults if needed."""
    settings_obj, created = ShopSettings.objects.get_or_create(user=user)
    if created:
        for i, name in enumerate(DEFAULT_CATEGORIES):
            ProductCategory.objects.create(settings=settings_obj, name=name, sort_order=i)
    return settings_obj


class ShopSettingsView(RetrieveUpdateAPIView):
    serializer_class   = ShopSettingsSerializer
    permission_classes = [IsAuthenticated]
    http_method_names  = ["get", "put"]

    def get_object(self):
        return get_or_create_settings(self.request.user)
