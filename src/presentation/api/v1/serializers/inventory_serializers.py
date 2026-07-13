from rest_framework import serializers


class StockAdjustmentSerializer(serializers.Serializer):
    item_id = serializers.IntegerField(min_value=1)
    warehouse_id = serializers.IntegerField(min_value=1)
    delta = serializers.IntegerField()
    reason = serializers.CharField(max_length=255)


class StockLevelResponseSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    qty_on_hand = serializers.IntegerField()
