from django.urls import path
from .views import SaleListCreateView, SaleDestroyView

urlpatterns = [
    path("",          SaleListCreateView.as_view(), name="sale-list"),
    path("<int:pk>/", SaleDestroyView.as_view(),    name="sale-delete"),
]
