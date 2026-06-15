"""
Dashboard API — GET /api/dashboard/

Returns all data needed to render the dashboard tab in one request:
  - Personal draw (net profit for current month)
  - Revenue, total costs, items in stock, loan remaining
  - Top-selling category this month
  - Low-stock alerts
  - 5 most recent sales

All numbers are computed server-side from PostgreSQL — no localStorage.
"""

from datetime import date
from decimal import Decimal

from django.db.models import Sum, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.purchases.models import Purchase
from apps.sales.models import Sale, SaleItem
from apps.shop_settings.views import get_or_create_settings
from apps.other_costs.models import OtherCost


def stock_by_category(user):
    """
    Returns a dict: {category: {in_stock, value, avg_cpp}}
    Computed as: sellable_purchased - sold for each category.
    """
    settings_obj = get_or_create_settings(user)
    cats = list(settings_obj.categories.values_list("name", flat=True))

    # Total sellable purchased per category
    purchased = dict(
        Purchase.objects
        .filter(user=user)
        .values("category")
        .annotate(
            total_sellable=Sum("sellable_pieces"),
            total_cost=Sum("total_cost"),
        )
        .values_list("category", "total_sellable")
    )

    purchased_cost = dict(
        Purchase.objects
        .filter(user=user)
        .values("category")
        .annotate(total_cost=Sum("total_cost"), total_sell=Sum("sellable_pieces"))
        .values_list("category", "total_cost")
    )
    purchased_sell = dict(
        Purchase.objects
        .filter(user=user)
        .values("category")
        .annotate(total_sell=Sum("sellable_pieces"))
        .values_list("category", "total_sell")
    )

    # Total sold per category
    sold = dict(
        SaleItem.objects
        .filter(sale__user=user)
        .values("category")
        .annotate(total_sold=Sum("quantity"))
        .values_list("category", "total_sold")
    )

    result = {}
    for cat in cats:
        total_buy  = purchased.get(cat, 0) or 0
        total_sell = purchased_sell.get(cat, 0) or 0
        total_cost = purchased_cost.get(cat, Decimal("0")) or Decimal("0")
        total_sold = sold.get(cat, 0) or 0
        in_stock   = max(0, total_buy - total_sold)
        avg_cpp    = (total_cost / total_sell) if total_sell > 0 else Decimal("0")
        result[cat] = {
            "in_stock": in_stock,
            "value":    float(in_stock * avg_cpp),
            "avg_cpp":  float(avg_cpp),
        }
    return result


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = date.today()
        mo, yr = today.month, today.year

        settings_obj = get_or_create_settings(user)
        s = settings_obj

        # ── Current month revenue ─────────────────────────────────────────────
        revenue = Sale.objects.filter(
            user=user, date__year=yr, date__month=mo
        ).aggregate(total=Sum("total_revenue"))["total"] or Decimal("0")

        # ── Current month COGS ────────────────────────────────────────────────
        cogs = Purchase.objects.filter(
            user=user, date__year=yr, date__month=mo
        ).aggregate(total=Sum("total_cost"))["total"] or Decimal("0")

        # ── Monthly other costs from OtherCost entries ────────────────────────
        fixed = OtherCost.objects.filter(
            user=user, date__year=yr, date__month=mo
        ).aggregate(t=Sum("amount"))["t"] or Decimal("0")

        # ── Net profit ────────────────────────────────────────────────────────
        net = revenue - cogs - fixed

        # ── Loan remaining (all-time repayments) ──────────────────────────────
        total_repaid = OtherCost.objects.filter(
            user=user,
            category__in=[OtherCost.LOAN_REPAYMENT, OtherCost.EXTRA_REPAYMENT],
        ).aggregate(t=Sum("amount"))["t"] or Decimal("0")
        loan_remaining = max(Decimal("0"), s.loan_total - total_repaid)

        # ── Stock ─────────────────────────────────────────────────────────────
        stock = stock_by_category(user)
        total_in_stock = sum(v["in_stock"] for v in stock.values())

        # ── Top-selling category this month ───────────────────────────────────
        top_cats = (
            SaleItem.objects
            .filter(sale__user=user, sale__date__year=yr, sale__date__month=mo)
            .values("category")
            .annotate(total_qty=Sum("quantity"))
            .order_by("-total_qty")
            .first()
        )

        # ── Low-stock alerts ──────────────────────────────────────────────────
        low_threshold = s.low_stock_threshold
        alerts = [
            {"category": cat, "in_stock": data["in_stock"], "status": "out" if data["in_stock"] == 0 else "low"}
            for cat, data in stock.items()
            if data["in_stock"] <= low_threshold
        ]

        # ── Recent sales ──────────────────────────────────────────────────────
        recent_sales = (
            Sale.objects
            .filter(user=user)
            .prefetch_related("items")
            .order_by("-date", "-created_at")[:5]
        )
        recent = [
            {
                "id":            s.id,
                "date":          s.date.isoformat(),
                "sale_type":     s.sale_type,
                "total_revenue": float(s.total_revenue),
                "notes":         s.notes,
                "items":         [{"category": i.category, "quantity": i.quantity} for i in s.items.all()],
            }
            for s in recent_sales
        ]

        return Response({
            "month":          today.strftime("%B %Y"),
            "net_profit":     float(net),
            "revenue":        float(revenue),
            "total_costs":    float(fixed + cogs),
            "total_in_stock": total_in_stock,
            "loan_remaining": float(loan_remaining),
            "top_category":   top_cats["category"] if top_cats else None,
            "top_qty":        top_cats["total_qty"] if top_cats else 0,
            "low_stock_alerts": alerts,
            "recent_sales":   recent,
        })
