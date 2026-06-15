"""
OtherCost — manually entered monthly costs and loan repayments.

Each entry records one payment: rent, wages, tax, a regular loan
repayment, an extra repayment, or any other cost.

Finance page uses this table instead of fixed ShopSettings fields so
that actual spending per month is tracked individually.
"""

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


class OtherCost(models.Model):
    RENT            = 'rent'
    WAGES           = 'wages'
    TAX             = 'tax'
    LOAN_REPAYMENT  = 'loan_repayment'
    EXTRA_REPAYMENT = 'extra_repayment'
    OTHER           = 'other'

    CATEGORY_CHOICES = [
        (RENT,            'Rent'),
        (WAGES,           'Wages'),
        (TAX,             'Tax'),
        (LOAN_REPAYMENT,  'Loan Repayment'),
        (EXTRA_REPAYMENT, 'Extra Repayment'),
        (OTHER,           'Other'),
    ]

    user     = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='other_costs'
    )
    date     = models.DateField(db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount   = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    notes      = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'other_cost'
        ordering = ['-date', '-created_at']
        indexes  = [models.Index(fields=['user', 'date'])]

    def __str__(self):
        return f"{self.date} {self.category} KES {self.amount}"
