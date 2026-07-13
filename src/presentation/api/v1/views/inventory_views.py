from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from src.application.inventory.services.inventory_service import InventoryService
from src.infrastructure.persistence.repositories.inventory_repository import DjangoInventoryRepository
from src.presentation.api.v1.serializers.inventory_serializers import StockAdjustmentSerializer


class StockAdjustmentAPIView(APIView):
    def post(self, request):
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = InventoryService(inventory_repository=DjangoInventoryRepository())
        service.adjust_stock(**serializer.validated_data)

        return Response({"status": "ok"}, status=status.HTTP_200_OK)
