from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Tuple

from django.db import transaction
from django.utils import timezone

from payouts.models import PayoutRequest, PayoutStatus


@dataclass(frozen=True)
class CreatePayoutDTO:
    client_reference: str
    amount: Decimal
    currency: str
    destination: str


@transaction.atomic
def create_payout_request(dto: CreatePayoutDTO) -> Tuple[PayoutRequest, bool]:
    """
    Idempotent create:
    - If client_reference is new -> create payout (created=True)
    - If already exists -> return existing (created=False)
    """
    obj, created = PayoutRequest.objects.get_or_create(
        client_reference=dto.client_reference,
        defaults={
            "amount": dto.amount,
            "currency": dto.currency,
            "destination": dto.destination,
            "status": PayoutStatus.NEW,
        },
    )
    return obj, created


@transaction.atomic
def mark_processing(payout_id) -> bool:
    """
    Switch NEW -> PROCESSING atomically.
    Returns True if status was changed, False if payout already processed/canceled.
    """
    updated = (
        PayoutRequest.objects
        .filter(id=payout_id, status=PayoutStatus.NEW)
        .update(status=PayoutStatus.PROCESSING)
    )
    return updated == 1


@transaction.atomic
def mark_paid(payout_id) -> None:
    PayoutRequest.objects.filter(id=payout_id).update(
        status=PayoutStatus.PAID,
        processed_at=timezone.now(),
        failure_reason="",
    )


@transaction.atomic
def mark_failed(payout_id, reason: str) -> None:
    PayoutRequest.objects.filter(id=payout_id).update(
        status=PayoutStatus.FAILED,
        processed_at=timezone.now(),
        failure_reason=reason,
    )


@transaction.atomic
def cancel_payout(payout_id) -> bool:
    """
    Allow cancel only for NEW or PROCESSING.
    Returns True if canceled, False if not allowed (e.g. PAID/FAILED/CANCELED).
    """
    updated = PayoutRequest.objects.filter(
        id=payout_id,
        status__in=[PayoutStatus.NEW, PayoutStatus.PROCESSING],
    ).update(status=PayoutStatus.CANCELED, processed_at=timezone.now())
    return updated == 1

