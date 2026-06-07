"""
Finance API — GET /api/finance/?year=YYYY&month=MM

Returns P&L breakdown for the requested month:
  - Revenue (total sales)
  - COGS (stock purchased)
  - Gross profit
  - Fixed costs breakdown (rent, wages, other, tax/12, loan repayment)
  - Net profit
  - Loan status (original, repaid, remaining, % progress)

Also returns the stock-value breakdown for the stock tab:
  GET /api/finance/stock/  — current stock levels per category
"""

from decimal import Decimal

from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.purchases.models import Purchase
from apps.sales.models import Sale
from apps.shop_settings.views import get_or_create_settings
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

        # Monthly fixed costs
        monthly_tax  = s.tax / 12
        total_fixed  = s.rent + s.wages + s.other + monthly_tax + s.loan_monthly
        net_profit   = gross_profit - total_fixed

        # Loan
        total_repaid   = s.loan_months_paid * s.loan_monthly
        loan_remaining = max(Decimal("0"), s.loan_total - total_repaid)
        loan_pct       = (
            float(total_repaid / s.loan_total * 100)
            if s.loan_total > 0
            else 0.0
        )

        return Response({
            "year":  year,
            "month": month,
            "revenue":      float(revenue),
            "cogs":         float(cogs),
            "gross_profit": float(gross_profit),
            "costs": {
                "rent":        float(s.rent),
                "wages":       float(s.wages),
                "other":       float(s.other),
                "tax_monthly": float(monthly_tax),
                "loan_monthly": float(s.loan_monthly),
                "total":       float(total_fixed),
            },
            "net_profit": float(net_profit),
            "loan": {
                "total":          float(s.loan_total),
                "months_paid":    s.loan_months_paid,
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
