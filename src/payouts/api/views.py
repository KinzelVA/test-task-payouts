from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from payouts.models import PayoutRequest
from payouts.api.serializers import PayoutRequestCreateSerializer, PayoutRequestSerializer
from payouts.services import CreatePayoutDTO, cancel_payout, create_payout_request
from payouts.tasks import process_payout_request


class PayoutRequestViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = PayoutRequest.objects.all().order_by("-created_at")
    serializer_class = PayoutRequestSerializer

    def create(self, request, *args, **kwargs):
        s = PayoutRequestCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        payout, created = create_payout_request(CreatePayoutDTO(**s.validated_data))

        # Trigger async processing only for newly created payouts
        if created:
            process_payout_request.delay(str(payout.id))
            return Response(PayoutRequestSerializer(payout).data, status=status.HTTP_201_CREATED)

        # Idempotent response: already existed
        return Response(PayoutRequestSerializer(payout).data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True, url_path="cancel")
    def cancel(self, request, pk=None):
        ok = cancel_payout(pk)
        payout = self.get_object()

        if not ok:
            raise ValidationError("Only NEW/PROCESSING payouts can be canceled.")

        return Response(PayoutRequestSerializer(payout).data, status=status.HTTP_200_OK)

