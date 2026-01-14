import random
import time
from celery import shared_task

from payouts.services import mark_processing, mark_paid, mark_failed


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_payout_request(self, payout_id: str) -> None:
    if not mark_processing(payout_id):
        return

    time.sleep(1)

    if random.random() < 0.8:
        mark_paid(payout_id)
    else:
        mark_failed(payout_id, "Provider error: insufficient funds or timeout")
