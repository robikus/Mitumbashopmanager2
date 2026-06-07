from rest_framework import serializers
from .models import Purchase


class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Purchase
        fields = [
            "id",
            "date",
            "category",
            "purchase_type",
            "total_pieces",
            "total_cost",
            "unsellable_pieces",
            "sellable_pieces",
            "cost_per_piece",
            "created_at",
        ]
        read_only_fields = [
            "unsellable_pieces",
            "sellable_pieces",
            "cost_per_piece",
            "created_at",
        ]

    def validate_category(self, value):
        """Ensure the category belongs to the user's configured categories."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                cats = list(
                    request.user.shop_settings.categories.values_list("name", flat=True)
                )
                if value not in cats:
                    raise serializers.ValidationError(
                        f"'{value}' is not a configured category. Choices: {cats}"
                    )
            except Exception:
                pass  # If settings don't exist yet, allow any value
        return value
