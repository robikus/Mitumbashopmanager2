"""
Authentication models.

UserProfile — extends Django's built-in User with Cognito identity data.
PendingUser  — registration requests awaiting admin approval.
"""

from django.contrib.auth.models import User
from django.db import models


class PendingUser(models.Model):
    """
    Stores access requests submitted via the public /auth/register/ page.
    Admin reviews these and creates Cognito accounts for approved applicants.
    """

    class Status(models.TextChoices):
        PENDING  = "pending",  "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    name       = models.CharField(max_length=255)
    email      = models.EmailField(unique=True)
    phone      = models.CharField(max_length=30)
    status     = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "auth_pending_user"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} ({self.status})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # The Cognito `sub` claim — unique, immutable identifier for this user
    cognito_sub = models.CharField(max_length=64, unique=True, db_index=True)

    # Store tokens so we can refresh without re-login
    refresh_token = models.TextField(blank=True)
    access_token  = models.TextField(blank=True)
    id_token      = models.TextField(blank=True)

    last_payment = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "auth_user_profile"

    def __str__(self):
        return f"{self.user.email} ({self.cognito_sub[:8]}…)"
