"""
Sale and SaleItem models.

A Sale is one transaction; SaleItem records each category+quantity pair
within that transaction.  This mirrors the `items` array inside each sale
object in the original static app.
"""

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


class Sale(models.Model):
    B2C = "B2C"
    B2B = "B2B"
    SALE_TYPE_CHOICES = [
        (B2C, "B2C – Single customer"),
        (B2B, "B2B – Bundle to trader"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sales",
        db_index=True,
    )

    date  = models.DateField(db_index=True)
    sale_type = models.CharField(max_length=3, choices=SALE_TYPE_CHOICES, default=B2C)

    total_revenue = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Total revenue for this sale in KES",
    )
    notes = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sale"
        ordering = ["-date", "-created_at"]
        indexes  = [
            models.Index(fields=["user", "date"]),
        ]

    def __str__(self):
        return f"{self.date} {self.sale_type} KES {self.total_revenue}"


class SaleItem(models.Model):
    """One category+quantity line within a sale."""

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="items",
    )
    category = models.CharField(max_length=80, db_index=True)
    quantity  = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = "sale_item"

    def __str__(self):
        return f"{self.quantity}× {self.category}"
