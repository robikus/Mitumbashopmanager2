from django.urls import path
from . import views

app_name = "authentication"

urlpatterns = [
    path("login/",      views.login_redirect, name="login"),
    path("callback/",   views.callback,       name="callback"),
    path("logout/",     views.logout_view,    name="logout"),
    path("logged-out/", views.logged_out,     name="logged_out"),
]
