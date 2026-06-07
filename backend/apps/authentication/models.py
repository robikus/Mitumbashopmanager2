"""
UserProfile extends Django's built-in User with Cognito identity data.

Each Django User is linked 1:1 to a Cognito identity via the `cognito_sub`
field (the immutable UUID Cognito assigns each user at sign-up).
"""

from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # The Cognito `sub` claim — unique, immutable identifier for this user
    cognito_sub = models.CharField(max_length=64, unique=True, db_index=True)

    # Store tokens so we can refresh without re-login
    refresh_token = models.TextField(blank=True)
    access_token  = models.TextField(blank=True)
    id_token      = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "auth_user_profile"

    def __str__(self):
        return f"{self.user.email} ({self.cognito_sub[:8]}…)"
