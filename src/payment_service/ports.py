"""Ports used by the payment service.

The concrete adapters intentionally live in tests so that Copilot has to infer
mock and fake boundaries from stable interfaces rather than implementation
accidents.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from .models import Payment


class PaymentGateway(Protocol):
    """External payment provider boundary."""

    def request_authorization(
        self,
        *,
        order_id: str,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
    ) -> str:
        """Return a provider authorization identifier or raise TimeoutError."""


class PaymentRepository(Protocol):
    """Persistence boundary for idempotent payment creation."""

    def find_by_key(self, idempotency_key: str) -> Payment | None:
        """Return an existing payment for the key, when present."""

    def save(self, idempotency_key: str, payment: Payment) -> None:
        """Persist the payment under the idempotency key."""
