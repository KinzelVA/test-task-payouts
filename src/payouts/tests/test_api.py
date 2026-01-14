from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from payouts.models import PayoutRequest, PayoutStatus


class PayoutRequestAPITests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = "/api/v1/payout-requests/"

    @patch("payouts.api.views.process_payout_request.delay")
    def test_create_returns_201_and_enqueues_task(self, delay_mock):
        payload = {
            "client_reference": "INV-90001",
            "amount": "1500.00",
            "currency": "rub",
            "destination": "card: 4111 **** **** 1111",
        }

        resp = self.client.post(self.url, payload, format="json")

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["client_reference"], "INV-90001")
        self.assertEqual(resp.data["status"], PayoutStatus.NEW)
        self.assertEqual(PayoutRequest.objects.count(), 1)

        delay_mock.assert_called_once()  # задача поставлена

    @patch("payouts.api.views.process_payout_request.delay")
    def test_idempotency_second_post_returns_200_and_no_second_task(self, delay_mock):
        payload = {
            "client_reference": "INV-90002",
            "amount": "1500.00",
            "currency": "rub",
            "destination": "wallet: test",
        }

        r1 = self.client.post(self.url, payload, format="json")
        self.assertEqual(r1.status_code, 201)
        created_id = r1.data["id"]

        r2 = self.client.post(self.url, payload, format="json")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["id"], created_id)

        self.assertEqual(PayoutRequest.objects.count(), 1)
        delay_mock.assert_called_once()  # только один раз

    @patch("payouts.api.views.process_payout_request.delay")
    def test_cancel_new_success(self, delay_mock):
        payload = {
            "client_reference": "INV-90003",
            "amount": "100.00",
            "currency": "rub",
            "destination": "wallet: cancel",
        }

        r1 = self.client.post(self.url, payload, format="json")
        self.assertEqual(r1.status_code, 201)
        pid = r1.data["id"]

        cancel_url = f"/api/v1/payout-requests/{pid}/cancel/"
        r2 = self.client.post(cancel_url, {}, format="json")

        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["status"], PayoutStatus.CANCELED)

    @patch("payouts.api.views.process_payout_request.delay")
    def test_cancel_paid_returns_400(self, delay_mock):
        payload = {
            "client_reference": "INV-90004",
            "amount": "100.00",
            "currency": "rub",
            "destination": "wallet: paid",
        }

        r1 = self.client.post(self.url, payload, format="json")
        self.assertEqual(r1.status_code, 201)
        pid = r1.data["id"]

        # вручную переводим в PAID, чтобы проверить запрет отмены
        pr = PayoutRequest.objects.get(id=pid)
        pr.status = PayoutStatus.PAID
        pr.save(update_fields=["status"])

        cancel_url = f"/api/v1/payout-requests/{pid}/cancel/"
        r2 = self.client.post(cancel_url, {}, format="json")

        self.assertEqual(r2.status_code, 400)
