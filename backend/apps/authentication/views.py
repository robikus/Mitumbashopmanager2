"""
Authentication views.

/auth/login/     — redirect to Cognito hosted UI
/auth/callback/  — exchange authorization code for tokens, log user in
/auth/logout/    — clear Django session + redirect to Cognito logout
"""

import hashlib
import hmac
import base64
import logging
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views.decorators.http import require_GET

from .models import UserProfile

logger = logging.getLogger(__name__)


def _client_secret_hash(username: str) -> str:
    """
    Cognito requires a HMAC-SHA256 hash of (username + client_id)
    when the app client has a secret.
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


# ── Views ─────────────────────────────────────────────────────────────────────

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
    Exchange the code for tokens, validate the ID token, and log the user in.
    """
    code = request.GET.get("code")
    error = request.GET.get("error")

    if error:
        logger.error("Cognito auth error: %s — %s", error, request.GET.get("error_description"))
        return redirect(f"/auth/login/?error={error}")

    if not code:
        return redirect("/auth/login/?error=missing_code")

    # Exchange code for tokens
    try:
        resp = requests.post(
            _cognito_token_endpoint(),
            data={
                "grant_type":   "authorization_code",
                "client_id":    settings.COGNITO_APP_CLIENT_ID,
                "client_secret": settings.COGNITO_APP_CLIENT_SECRET,
                "redirect_uri": _redirect_uri(),
                "code":         code,
            },
            timeout=10,
        )
        resp.raise_for_status()
        tokens = resp.json()
    except Exception as exc:
        logger.error("Token exchange failed: %s", exc)
        return redirect("/auth/login/?error=token_exchange_failed")

    id_token      = tokens.get("id_token", "")
    access_token  = tokens.get("access_token", "")
    refresh_token = tokens.get("refresh_token", "")

    # Validate the ID token and get (or create) the Django user
    user = authenticate(request, id_token=id_token)
    if user is None:
        logger.error("authenticate() returned None for id_token")
        return redirect("/auth/login/?error=invalid_token")

    # Persist tokens so we can refresh later without re-login
    try:
        profile = user.profile
        profile.id_token      = id_token
        profile.access_token  = access_token
        profile.refresh_token = refresh_token
        profile.save(update_fields=["id_token", "access_token", "refresh_token", "updated_at"])
    except UserProfile.DoesNotExist:
        pass

    login(request, user, backend="apps.authentication.backends.CognitoBackend")
    return redirect("/")


@require_GET
def logout_view(request):
    """Clear Django session and redirect to Cognito's logout endpoint."""
    logout(request)

    params = {
        "client_id":    settings.COGNITO_APP_CLIENT_ID,
        "redirect_uri": f"{settings.APP_DOMAIN}/auth/logged-out/",
    }
    url = f"{settings.COGNITO_DOMAIN}/logout?{urlencode(params)}"
    return HttpResponseRedirect(url)


@require_GET
def logged_out(request):
    """Landing page after Cognito logout."""
    return redirect("/auth/login/")


def spa_shell(request):
    """
    Serve the single-page app shell for authenticated users.
    Unauthenticated requests are redirected to the Cognito login page.
    """
    from django.shortcuts import render
    if not request.user.is_authenticated:
        return login_redirect(request)
    return render(request, "index.html", {
        "user_email": request.user.email,
        "cognito_domain": settings.COGNITO_DOMAIN,
        "app_client_id":  settings.COGNITO_APP_CLIENT_ID,
    })
