"""
CognitoBackend — Django authentication backend.

Validates a Cognito ID token JWT and returns (or creates) the matching
Django User.  Called by django.contrib.auth.authenticate() when
`backend='apps.authentication.backends.CognitoBackend'` is passed.

Token validation follows the Cognito developer guide:
  https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
"""

import logging
from urllib.request import urlopen
import json

from django.conf import settings
from django.contrib.auth.models import User

from jose import jwk, jwt
from jose.utils import base64url_decode

from .models import UserProfile

logger = logging.getLogger(__name__)

_JWKS_CACHE: dict = {}


def _get_jwks() -> dict:
    """Fetch and cache Cognito's public keys (JWKS)."""
    global _JWKS_CACHE
    if _JWKS_CACHE:
        return _JWKS_CACHE

    pool_id = settings.COGNITO_USER_POOL_ID
    region  = settings.COGNITO_REGION
    url = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"

    with urlopen(url, timeout=5) as resp:
        _JWKS_CACHE = json.loads(resp.read())

    return _JWKS_CACHE


def validate_id_token(id_token: str) -> dict:
    """
    Validate a Cognito ID token and return its claims dict.
    Raises jose.JWTError on any validation failure.
    """
    jwks = _get_jwks()

    # Decode header to get `kid` without verifying signature yet
    headers = jwt.get_unverified_headers(id_token)
    kid = headers["kid"]

    # Find the matching public key
    key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
    if key is None:
        raise ValueError(f"Public key {kid!r} not found in JWKS")

    public_key = jwk.construct(key)

    # Verify signature
    message, encoded_sig = id_token.rsplit(".", 1)
    decoded_sig = base64url_decode(encoded_sig.encode("utf-8"))
    if not public_key.verify(message.encode("utf-8"), decoded_sig):
        raise ValueError("Token signature verification failed")

    # Verify claims
    claims = jwt.get_unverified_claims(id_token)

    pool_id  = settings.COGNITO_USER_POOL_ID
    region   = settings.COGNITO_REGION
    issuer   = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}"
    audience = settings.COGNITO_APP_CLIENT_ID

    if claims.get("iss") != issuer:
        raise ValueError(f"Invalid issuer: {claims.get('iss')}")
    if claims.get("aud") != audience:
        raise ValueError(f"Invalid audience: {claims.get('aud')}")
    if claims.get("token_use") != "id":
        raise ValueError("Token is not an ID token")

    return claims


class CognitoBackend:
    """
    Custom authentication backend that validates a Cognito ID token and
    maps it to a Django User.

    Usage:
        user = authenticate(request, id_token="eyJ...")
    """

    def authenticate(self, request, id_token: str = None, **kwargs):
        if not id_token:
            return None

        try:
            claims = validate_id_token(id_token)
        except Exception as exc:
            logger.warning("Cognito token validation failed: %s", exc)
            return None

        cognito_sub = claims["sub"]
        email = claims.get("email", "")

        try:
            profile = UserProfile.objects.select_related("user").get(cognito_sub=cognito_sub)
            user = profile.user
            # Keep email in sync in case it changed in Cognito
            if user.email != email:
                user.email = email
                user.username = email
                user.save(update_fields=["email", "username"])
        except UserProfile.DoesNotExist:
            # First login — create the Django user
            user = User.objects.create_user(
                username=email,
                email=email,
                password=None,  # No password — auth is via Cognito only
            )
            UserProfile.objects.create(user=user, cognito_sub=cognito_sub)

        return user

    def get_user(self, user_id: int):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
