"""
CognitoSessionRefreshMiddleware

Transparently refreshes the Cognito access token when it expires.
This prevents the user from being kicked to the login page just because
the 1-hour access token expired — the refresh token is valid for 30 days.
"""

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class CognitoSessionRefreshMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only attempt refresh for authenticated users hitting API endpoints
        if (
            request.user.is_authenticated
            and request.path.startswith("/api/")
        ):
            self._maybe_refresh(request)

        return self.get_response(request)

    def _maybe_refresh(self, request):
        try:
            profile = request.user.profile
        except Exception:
            return

        if not profile.refresh_token:
            return

        # Attempt refresh — Cognito will reject expired access tokens
        # We check by calling the /oauth2/userInfo endpoint
        resp = requests.get(
            f"{settings.COGNITO_DOMAIN}/oauth2/userInfo",
            headers={"Authorization": f"Bearer {profile.access_token}"},
            timeout=3,
        )

        if resp.status_code == 200:
            return  # Token still valid

        # Token expired — try to get a new one using the refresh token
        try:
            token_resp = requests.post(
                f"{settings.COGNITO_DOMAIN}/oauth2/token",
                data={
                    "grant_type":    "refresh_token",
                    "client_id":     settings.COGNITO_APP_CLIENT_ID,
                    "client_secret": settings.COGNITO_APP_CLIENT_SECRET,
                    "refresh_token": profile.refresh_token,
                },
                timeout=5,
            )
            token_resp.raise_for_status()
            tokens = token_resp.json()
            profile.access_token = tokens.get("access_token", profile.access_token)
            profile.id_token     = tokens.get("id_token", profile.id_token)
            profile.save(update_fields=["access_token", "id_token", "updated_at"])
        except Exception as exc:
            logger.warning("Token refresh failed for user %s: %s", request.user.id, exc)
