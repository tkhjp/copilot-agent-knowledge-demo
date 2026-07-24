"""Domain models for the payment example."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class PaymentStatus(str, Enum):
    """Lifecycle states exposed by the demo payment service."""

    AUTHORIZED = "authorized"


@dataclass(frozen=True, slots=True)
class Order:
    """An order that can be authorized for payment."""

    order_id: str
    amount: Decimal
    currency: str = "JPY"


@dataclass(frozen=True, slots=True)
class Payment:
    """A successful payment authorization."""

    payment_id: str
    order_id: str
    amount: Decimal
    currency: str
    status: PaymentStatus = PaymentStatus.AUTHORIZED
