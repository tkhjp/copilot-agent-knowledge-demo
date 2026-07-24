from __future__ import annotations

import unittest
from decimal import Decimal

from payment_service.models import Order, Payment
from payment_service.service import (
    InvalidAmountError,
    PaymentGatewayUnavailable,
    PaymentService,
)


class FakeGateway:
    def __init__(self, responses: list[str | BaseException]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def request_authorization(self, **request: object) -> str:
        self.calls.append(request)
        response = self._responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class InMemoryPaymentRepository:
    def __init__(self) -> None:
        self._by_key: dict[str, Payment] = {}
        self.saved: list[tuple[str, Payment]] = []

    def find_by_key(self, idempotency_key: str) -> Payment | None:
        return self._by_key.get(idempotency_key)

    def save(self, idempotency_key: str, payment: Payment) -> None:
        self._by_key[idempotency_key] = payment
        self.saved.append((idempotency_key, payment))


class PaymentServiceTest(unittest.TestCase):
    def test_authorizes_and_persists_payment(self) -> None:
        gateway = FakeGateway(["pay-100"])
        repository = InMemoryPaymentRepository()
        service = PaymentService(gateway, repository)

        payment = service.authorize(
            Order("order-1", Decimal("1200")),
            "key-1",
        )

        self.assertEqual("pay-100", payment.payment_id)
        self.assertEqual(1, len(gateway.calls))
        self.assertEqual([("key-1", payment)], repository.saved)

    def test_rejects_non_positive_amount_before_dependencies(self) -> None:
        gateway = FakeGateway(["unused"])
        repository = InMemoryPaymentRepository()
        service = PaymentService(gateway, repository)

        with self.assertRaisesRegex(InvalidAmountError, "positive"):
            service.authorize(Order("order-1", Decimal("0")), "key-1")

        self.assertEqual([], gateway.calls)
        self.assertEqual([], repository.saved)

    def test_retries_once_then_translates_second_timeout(self) -> None:
        gateway = FakeGateway([TimeoutError(), TimeoutError()])
        repository = InMemoryPaymentRepository()
        service = PaymentService(gateway, repository)

        with self.assertRaisesRegex(PaymentGatewayUnavailable, "twice"):
            service.authorize(Order("order-1", Decimal("1200")), "key-1")

        self.assertEqual(2, len(gateway.calls))
        self.assertEqual([], repository.saved)


if __name__ == "__main__":
    unittest.main()
