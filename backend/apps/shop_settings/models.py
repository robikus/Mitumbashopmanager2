"""
ShopSettings — per-user configuration.

Mirrors the `S.settings` object from the original static app.
Each registered user gets exactly one ShopSettings row (created on first
access via get_or_create).
"""

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class ShopSettings(models.Model):
    """Top-level settings for one user's shop."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="shop_settings",
    )

    shop_name = models.CharField(max_length=120, default="My Mitumba Shop")

    # ── Loan ──────────────────────────────────────────────────────────────────
    # Monthly costs and loan repayments are logged individually in OtherCost.
    loan_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # ── Bale settings ─────────────────────────────────────────────────────────
    unsellable_rate = models.PositiveSmallIntegerField(
        default=20,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of pieces per bale that are damaged/unsellable",
    )

    # ── Alerts ────────────────────────────────────────────────────────────────
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        help_text="Show low-stock warning when any category falls below this number",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shop_settings"
        verbose_name = "Shop Settings"
        verbose_name_plural = "Shop Settings"

    def __str__(self):
        return f"{self.shop_name} ({self.user.email})"


class ProductCategory(models.Model):
    """
    Named product category owned by one user (up to 10 per shop).
    Used to group purchases and sales items.
    """

    settings = models.ForeignKey(
        ShopSettings,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField(max_length=80)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "shop_product_category"
        unique_together = [("settings", "name")]
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name
