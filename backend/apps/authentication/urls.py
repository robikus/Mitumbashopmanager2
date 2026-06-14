from django.urls import path
from . import views

app_name = "authentication"

urlpatterns = [
    # OAuth2 / Cognito
    path("login/",      views.login_redirect, name="login"),
    path("callback/",   views.callback,       name="callback"),
    path("logout/",     views.logout_view,    name="logout"),
    path("logged-out/", views.logged_out,     name="logged_out"),

    # Public registration (no auth required)
    path("register/", views.register, name="register"),

    # Admin approval panel (staff only)
    path("admin/pending/",              views.admin_pending_users, name="admin_pending_users"),
    path("admin/approve/<int:user_id>/", views.admin_approve_user, name="admin_approve_user"),
    path("admin/reject/<int:user_id>/",  views.admin_reject_user,  name="admin_reject_user"),
]
