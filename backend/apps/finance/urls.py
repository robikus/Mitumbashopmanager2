from django.urls import path
from .views import FinanceView, StockView

urlpatterns = [
    path("",       FinanceView.as_view(), name="finance"),
    path("stock/", StockView.as_view(),   name="stock"),
]
