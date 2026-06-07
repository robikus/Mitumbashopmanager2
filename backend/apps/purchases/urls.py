from django.urls import path
from .views import PurchaseListCreateView, PurchaseDestroyView

urlpatterns = [
    path("",         PurchaseListCreateView.as_view(), name="purchase-list"),
    path("<int:pk>/", PurchaseDestroyView.as_view(),   name="purchase-delete"),
]
