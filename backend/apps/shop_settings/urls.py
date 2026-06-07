from django.urls import path
from .views import ShopSettingsView

urlpatterns = [
    path("", ShopSettingsView.as_view(), name="shop-settings"),
]
