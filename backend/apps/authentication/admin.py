"""
Django admin registration for authentication models.

PendingUser — visible at /admin/authentication/pendinguser/
Approve/reject actions call the Cognito API directly from the admin.
"""

import boto3
from botocore.exceptions import ClientError

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.models import User, Group

from .models import PendingUser, UserProfile

# Remove built-in auth models — users are managed via Cognito
admin.site.unregister(User)
admin.site.unregister(Group)


# ---------------------------------------------------------------------------
# Admin actions
# ---------------------------------------------------------------------------

@admin.action(description="Approve selected users — create Cognito accounts")
def approve_users(modeladmin, request, queryset):
    client = boto3.client("cognito-idp", region_name=settings.COGNITO_REGION)
    for pending in queryset.filter(status=PendingUser.Status.PENDING):
        try:
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
                f"{pending.email} approved — temporary password sent by email.",
            )
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code == "UsernameExistsException":
                pending.status = PendingUser.Status.APPROVED
                pending.save(update_fields=["status", "updated_at"])
                messages.warning(
                    request,
                    f"{pending.email} already exists in Cognito — marked approved.",
                )
            else:
                messages.error(
                    request,
                    f"{pending.email}: {exc.response['Error']['Message']}",
                )


@admin.action(description="Reject selected users")
def reject_users(modeladmin, request, queryset):
    updated = queryset.filter(status=PendingUser.Status.PENDING).update(
        status=PendingUser.Status.REJECTED
    )
    messages.info(request, f"{updated} user(s) rejected.")


# ---------------------------------------------------------------------------
# Model admin classes
# ---------------------------------------------------------------------------

@admin.register(PendingUser)
class PendingUserAdmin(admin.ModelAdmin):
    list_display  = ("name", "email", "phone", "status", "created_at")
    list_filter   = ("status",)
    search_fields = ("name", "email", "phone")
    readonly_fields = ("created_at", "updated_at")
    ordering      = ("-created_at",)
    actions       = [approve_users, reject_users]

    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display    = ("user", "cognito_sub", "created_at")
    search_fields   = ("user__email", "cognito_sub")
    readonly_fields = ("cognito_sub", "created_at", "updated_at",
                       "access_token", "id_token", "refresh_token")
    ordering        = ("-created_at",)

    def has_add_permission(self, request):
        return False
