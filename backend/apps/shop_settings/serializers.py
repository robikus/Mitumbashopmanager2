from rest_framework import serializers
from .models import ShopSettings, ProductCategory


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductCategory
        fields = ["id", "name", "sort_order"]


class ShopSettingsSerializer(serializers.ModelSerializer):
    categories = ProductCategorySerializer(many=True)

    class Meta:
        model = ShopSettings
        fields = [
            "shop_name",
            "loan_total",
            "unsellable_rate",
            "low_stock_threshold",
            "categories",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def update(self, instance, validated_data):
        # Handle nested categories: replace the entire list
        cats_data = validated_data.pop("categories", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if cats_data is not None:
            instance.categories.all().delete()
            for i, cat in enumerate(cats_data):
                ProductCategory.objects.create(
                    settings=instance,
                    name=cat["name"],
                    sort_order=i,
                )

        return instance
