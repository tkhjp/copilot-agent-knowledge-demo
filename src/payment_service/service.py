"""Application service containing the behavior used by the demo.

The service is deliberately small but has several branches that are useful for
showing how a code graph and a high-signal knowledge projection can guide test
generation.
"""

from __future__ import annotations

from .models import Order, Payment
from .ports import PaymentGateway, PaymentRepository


class InvalidAmountError(ValueError):
    """Raised when an order amount is not strictly positive."""


class PaymentGatewayUnavailable(RuntimeError):
    """Raised after the gateway times out twice."""


class PaymentService:
    """Authorize payments while enforcing validation and idempotency."""

    def __init__(
        self,
        gateway: PaymentGateway,
        repository: PaymentRepository,
    ) -> None:
        self._gateway = gateway
        self._repository = repository

    def authorize(self, order: Order, idempotency_key: str) -> Payment:
        """Authorize an order.

        Rules:
        - non-positive amounts are rejected before any dependency is called;
        - an existing idempotency key returns the original payment;
        - one gateway timeout is retried;
        - a second timeout is translated to PaymentGatewayUnavailable;
        - persistence happens only after a successful gateway authorization.
        """

        if order.amount <= 0:
            raise InvalidAmountError("order amount must be positive")

        existing = self._repository.find_by_key(idempotency_key)
        if existing is not None:
            return existing

        try:
            payment_id = self._gateway.request_authorization(
                order_id=order.order_id,
                amount=order.amount,
                currency=order.currency,
                idempotency_key=idempotency_key,
            )
        except TimeoutError:
            try:
                payment_id = self._gateway.request_authorization(
                    order_id=order.order_id,
                    amount=order.amount,
                    currency=order.currency,
                    idempotency_key=idempotency_key,
                )
            except TimeoutError as exc:
                raise PaymentGatewayUnavailable(
                    "payment gateway timed out twice"
                ) from exc

        payment = Payment(
            payment_id=payment_id,
            order_id=order.order_id,
            amount=order.amount,
            currency=order.currency,
        )
        self._repository.save(idempotency_key, payment)
        return payment
