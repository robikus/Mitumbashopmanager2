"""
Purchase model — records each bale or single-piece stock acquisition.

Mirrors the purchase objects stored in S.purchases in the original app.
Sellable pieces and cost-per-piece are computed and stored (denormalised)
so queries are fast without recalculating every time.
"""

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


class Purchase(models.Model):
    SINGLE = "Single"
    BALE   = "Bale"
    PURCHASE_TYPE_CHOICES = [
        (SINGLE, "Single pieces"),
        (BALE,   "Bulk bale"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="purchases",
        db_index=True,
    )

    date     = models.DateField(db_index=True)
    category = models.CharField(max_length=80, db_index=True)

    purchase_type = models.CharField(
        max_length=10,
        choices=PURCHASE_TYPE_CHOICES,
        default=SINGLE,
    )

    total_pieces = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Total pieces in the purchase (before removing unsellable)",
    )
    total_cost = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Total cost in KES",
    )

    # Computed on save — stored for query performance
    unsellable_pieces = models.PositiveIntegerField(default=0)
    sellable_pieces   = models.PositiveIntegerField(default=0)
    cost_per_piece    = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Cost per sellable piece (KES)",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = "purchase"
        ordering  = ["-date", "-created_at"]
        indexes   = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["user", "category"]),
        ]

    def save(self, *args, **kwargs):
        """Compute derived fields before saving."""
        from apps.shop_settings.views import get_or_create_settings
        settings_obj = get_or_create_settings(self.user)
        unsell_rate  = settings_obj.unsellable_rate / 100

        if self.purchase_type == self.BALE:
            self.unsellable_pieces = round(self.total_pieces * unsell_rate)
        else:
            self.unsellable_pieces = 0

        self.sellable_pieces = self.total_pieces - self.unsellable_pieces
        if self.sellable_pieces > 0:
            self.cost_per_piece = self.total_cost / self.sellable_pieces
        else:
            self.cost_per_piece = 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} {self.category} {self.purchase_type} ({self.sellable_pieces} sellable)"
