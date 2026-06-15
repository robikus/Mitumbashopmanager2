from django.urls import path
from . import views

urlpatterns = [
    path('',          views.OtherCostListCreateView.as_view()),
    path('<int:pk>/', views.OtherCostDestroyView.as_view()),
]
