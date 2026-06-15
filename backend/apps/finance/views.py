"""
Finance API

GET /api/finance/?year=YYYY&month=MM
  Returns P&L for the requested month using actual OtherCost entries.

GET /api/finance/stock/
  Returns current stock levels per category.
"""

from decimal import Decimal

from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.purchases.models import Purchase
from apps.sales.models import Sale
from apps.shop_settings.views import get_or_create_settings
from apps.other_costs.models import OtherCost
from apps.dashboard.views import stock_by_category


class FinanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            year  = int(request.query_params.get("year",  0))
            month = int(request.query_params.get("month", 0))
            if not (1 <= month <= 12 and year >= 2000):
                raise ValueError
        except (ValueError, TypeError):
            from datetime import date
            today = date.today()
            year, month = today.year, today.month

        s = get_or_create_settings(user)

        revenue = Sale.objects.filter(
            user=user, date__year=year, date__month=month
        ).aggregate(t=Sum("total_revenue"))["t"] or Decimal("0")

        cogs = Purchase.objects.filter(
            user=user, date__year=year, date__month=month
        ).aggregate(t=Sum("total_cost"))["t"] or Decimal("0")

        gross_profit = revenue - cogs

        def month_sum(cat):
            return float(
                OtherCost.objects.filter(
                    user=user, date__year=year, date__month=month, category=cat
                ).aggregate(t=Sum("amount"))["t"] or Decimal("0")
            )

        costs = {
            "rent":            month_sum(OtherCost.RENT),
            "wages":           month_sum(OtherCost.WAGES),
            "tax":             month_sum(OtherCost.TAX),
            "loan_repayment":  month_sum(OtherCost.LOAN_REPAYMENT),
            "extra_repayment": month_sum(OtherCost.EXTRA_REPAYMENT),
            "other":           month_sum(OtherCost.OTHER),
        }
        costs["total"] = sum(costs.values())

        net_profit = float(gross_profit) - costs["total"]

        # Loan: sum all-time repayments (not just this month)
        total_repaid = OtherCost.objects.filter(
            user=user,
            category__in=[OtherCost.LOAN_REPAYMENT, OtherCost.EXTRA_REPAYMENT],
        ).aggregate(t=Sum("amount"))["t"] or Decimal("0")

        loan_remaining = max(Decimal("0"), s.loan_total - total_repaid)
        loan_pct = (
            float(total_repaid / s.loan_total * 100)
            if s.loan_total > 0 else 0.0
        )

        return Response({
            "year":         year,
            "month":        month,
            "revenue":      float(revenue),
            "cogs":         float(cogs),
            "gross_profit": float(gross_profit),
            "costs":        costs,
            "net_profit":   net_profit,
            "loan": {
                "total":          float(s.loan_total),
                "total_repaid":   float(total_repaid),
                "remaining":      float(loan_remaining),
                "percent_repaid": round(loan_pct, 1),
            },
        })


class StockView(APIView):
    """GET /api/finance/stock/ — current stock levels per category."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user  = request.user
        stock = stock_by_category(user)

        total_pieces = sum(v["in_stock"] for v in stock.values())
        total_value  = sum(v["value"]    for v in stock.values())

        categories = [
            {
                "category": cat,
                "in_stock": data["in_stock"],
                "value":    round(data["value"], 2),
                "avg_cpp":  round(data["avg_cpp"], 2),
            }
            for cat, data in stock.items()
        ]

        return Response({
            "categories":   categories,
            "total_pieces": total_pieces,
            "total_value":  round(total_value, 2),
        })
