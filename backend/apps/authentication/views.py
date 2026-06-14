"""
Authentication views.

/auth/login/          - redirect to Cognito hosted UI
/auth/callback/       - exchange authorization code for tokens, log user in
/auth/logout/         - clear Django session + redirect to login
/auth/register/       - public registration form (stores PendingUser)
/auth/admin/pending/  - admin: list + approve/reject pending users
"""

import hashlib
import hmac
import base64
import logging
from urllib.parse import urlencode

import boto3
import requests
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import (
    require_GET,
    require_POST,
    require_http_methods,
)

from .models import PendingUser, UserProfile

logger = logging.getLogger(__name__)


def _client_secret_hash(username: str) -> str:
    """
    Cognito requires HMAC-SHA256 of (username + client_id) when the app
    client has a secret.
    """
    message = username + settings.COGNITO_APP_CLIENT_ID
    dig = hmac.new(
        settings.COGNITO_APP_CLIENT_SECRET.encode("utf-8"),
        msg=message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode()


def _cognito_token_endpoint() -> str:
    return f"{settings.COGNITO_DOMAIN}/oauth2/token"


def _redirect_uri() -> str:
    return f"{settings.APP_DOMAIN}/auth/callback/"


# ---------------------------------------------------------------------------
# Login / OAuth2
# ---------------------------------------------------------------------------

@require_GET
def login_redirect(request):
    """Redirect the browser to the Cognito hosted login page."""
    params = {
        "response_type": "code",
        "client_id": settings.COGNITO_APP_CLIENT_ID,
        "redirect_uri": _redirect_uri(),
        "scope": "email openid profile",
    }
    url = f"{settings.COGNITO_DOMAIN}/login?{urlencode(params)}"
    return HttpResponseRedirect(url)


@require_GET
def callback(request):
    """
    Cognito redirects here after successful login with ?code=...
    Exchange the code for tokens, validate the ID token, log the user in.
    """
    code = request.GET.get("code")
    error = request.GET.get("error")

    if error:
        desc = request.GET.get("error_description", "")
        logger.error("Cognito auth error: %s - %s", error, desc)
        return redirect(f"/auth/login/?error={error}")

    if not code:
        return redirect("/auth/login/?error=missing_code")

    try:
        resp = requests.post(
            _cognito_token_endpoint(),
            data={
                "grant_type": "authorization_code",
                "client_id": settings.COGNITO_APP_CLIENT_ID,
                "client_secret": settings.COGNITO_APP_CLIENT_SECRET,
                "redirect_uri": _redirect_uri(),
                "code": code,
            },
            timeout=10,
        )
        resp.raise_for_status()
        tokens = resp.json()
    except Exception as exc:
        logger.error("Token exchange failed: %s", exc)
        return redirect("/auth/login/?error=token_exchange_failed")

    id_token = tokens.get("id_token", "")
    access_token = tokens.get("access_token", "")
    refresh_token = tokens.get("refresh_token", "")

    user = authenticate(request, id_token=id_token)
    if user is None:
        logger.error("authenticate() returned None for id_token")
        return redirect("/auth/login/?error=invalid_token")

    try:
        profile = user.profile
        profile.id_token = id_token
        profile.access_token = access_token
        profile.refresh_token = refresh_token
        profile.save(
            update_fields=[
                "id_token", "access_token", "refresh_token", "updated_at"
            ]
        )
    except UserProfile.DoesNotExist:
        pass

    login(request, user, backend="apps.authentication.backends.CognitoBackend")
    return redirect("/")


@require_GET
def logout_view(request):
    """Clear Django session and redirect to login."""
    logout(request)
    return redirect("/auth/login/")


@require_GET
def logged_out(request):
    """Landing page after Cognito logout."""
    return redirect("/auth/login/")


def spa_shell(request):
    """
    Serve the SPA shell for authenticated users.
    Unauthenticated requests are redirected to the Cognito login page.
    """
    if not request.user.is_authenticated:
        return login_redirect(request)
    return render(request, "index.html", {
        "user_email": request.user.email,
        "cognito_domain": settings.COGNITO_DOMAIN,
        "app_client_id": settings.COGNITO_APP_CLIENT_ID,
    })


# ---------------------------------------------------------------------------
# Public registration
# ---------------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def register(request):
    """
    Public registration page. Collects name, email, and phone number.
    Saves a PendingUser for admin review - no Cognito account created yet.
    """
    if request.method == "GET":
        return render(request, "register.html", {})

    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip().lower()
    phone = request.POST.get("phone", "").strip()

    errors = {}
    if not name:
        errors["name"] = "Full name is required."
    if not email or "@" not in email:
        errors["email"] = "A valid email address is required."
    if not phone:
        errors["phone"] = "Phone number is required."

    if not errors and PendingUser.objects.filter(email=email).exists():
        errors["email"] = "An application for this email already exists."

    if errors:
        return render(request, "register.html", {
            "errors": errors,
            "name": name,
            "email": email,
            "phone": phone,
        })

    PendingUser.objects.create(name=name, email=email, phone=phone)
    return render(request, "register.html", {"submitted": True})


# ---------------------------------------------------------------------------
# Admin approval panel
# ---------------------------------------------------------------------------

@staff_member_required(login_url="/auth/login/")
@require_GET
def admin_pending_users(request):
    """List all pending registration requests."""
    users = PendingUser.objects.all()
    return render(request, "admin_pending_users.html", {"users": users})


@staff_member_required(login_url="/auth/login/")
@require_POST
def admin_approve_user(request, user_id):
    """
    Approve a pending user: create their Cognito account and send a temp
    password via email. The EC2 instance role must have
    cognito-idp:AdminCreateUser permission.
    """
    pending = get_object_or_404(PendingUser, id=user_id)

    if pending.status != PendingUser.Status.PENDING:
        messages.warning(
            request,
            f"{pending.email} is already "
            f"{pending.get_status_display().lower()}.",
        )
        return redirect("/auth/admin/pending/")

    try:
        client = boto3.client(
            "cognito-idp", region_name=settings.COGNITO_REGION
        )
        client.admin_create_user(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=pending.email,
            UserAttributes=[
                {"Name": "email", "Value": pending.email},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "name", "Value": pending.name},
            ],
            DesiredDeliveryMediums=["EMAIL"],
        )
        pending.status = PendingUser.Status.APPROVED
        pending.save(update_fields=["status", "updated_at"])
        messages.success(
            request,
            f"{pending.email} approved. A temporary password was sent "
            f"to their email.",
        )
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code == "UsernameExistsException":
            pending.status = PendingUser.Status.APPROVED
            pending.save(update_fields=["status", "updated_at"])
            messages.warning(
                request,
                f"{pending.email} already exists in Cognito - "
                f"marked as approved.",
            )
        else:
            logger.error(
                "Cognito AdminCreateUser failed for %s: %s",
                pending.email,
                exc,
            )
            messages.error(
                request,
                f"Cognito error: {exc.response['Error']['Message']}",
            )

    return redirect("/auth/admin/pending/")


@staff_member_required(login_url="/auth/login/")
@require_POST
def admin_reject_user(request, user_id):
    """Reject a pending registration request."""
    pending = get_object_or_404(PendingUser, id=user_id)
    pending.status = PendingUser.Status.REJECTED
    pending.admin_note = request.POST.get("note", "").strip()
    pending.save(update_fields=["status", "admin_note", "updated_at"])
    messages.info(request, f"{pending.email} rejected.")
    return redirect("/auth/admin/pending/")
