# Generated module knowledge: `payment_service`

> Generated deterministically. Verify claims against the current source before editing code.

## Responsibilities

- `payment_service.__init__`: Small payment domain used by the agent-knowledge demo.
- `payment_service.models`: Domain models for the payment example.
- `payment_service.ports`: Ports used by the payment service.
- `payment_service.service`: Application service containing the behavior used by the demo.

## Symbols

- `payment_service.models.Order` (class, `src/payment_service/models.py:17`) — An order that can be authorized for payment.
- `payment_service.models.Payment` (class, `src/payment_service/models.py:26`) — A successful payment authorization.
- `payment_service.models.PaymentStatus` (class, `src/payment_service/models.py:10`) — Lifecycle states exposed by the demo payment service.
- `payment_service.ports.PaymentGateway` (class, `src/payment_service/ports.py:16`) — External payment provider boundary.
- `payment_service.ports.PaymentRepository` (class, `src/payment_service/ports.py:30`) — Persistence boundary for idempotent payment creation.
- `payment_service.service.InvalidAmountError` (class, `src/payment_service/service.py:14`) — Raised when an order amount is not strictly positive.
- `payment_service.service.PaymentGatewayUnavailable` (class, `src/payment_service/service.py:18`) — Raised after the gateway times out twice.
- `payment_service.service.PaymentService` (class, `src/payment_service/service.py:22`) — Authorize payments while enforcing validation and idempotency.
- `payment_service.ports.PaymentGateway.request_authorization` (method, `src/payment_service/ports.py:19`) — Return a provider authorization identifier or raise TimeoutError.
- `payment_service.ports.PaymentRepository.find_by_key` (method, `src/payment_service/ports.py:33`) — Return an existing payment for the key, when present.
- `payment_service.ports.PaymentRepository.save` (method, `src/payment_service/ports.py:36`) — Persist the payment under the idempotency key.
- `payment_service.service.PaymentService.__init__` (method, `src/payment_service/service.py:25`) — No docstring.
- `payment_service.service.PaymentService.authorize` (method, `src/payment_service/service.py:33`) — Authorize an order.

## Static branch inventory

- `payment_service.service.PaymentService.authorize` at `src/payment_service/service.py:44`: `order.amount <= 0`
- `payment_service.service.PaymentService.authorize` at `src/payment_service/service.py:48`: `existing is not None`

## Raised exceptions

- `payment_service.service.PaymentService.authorize`: `InvalidAmountError`, `PaymentGatewayUnavailable`

## Outbound calls

- `payment_service.service.PaymentService.authorize` → `payment_service.models.Payment` (exact, `src/payment_service/service.py:71`)
- `payment_service.service.PaymentService.authorize` → `payment_service.service.InvalidAmountError` (exact, `src/payment_service/service.py:45`)
- `payment_service.service.PaymentService.authorize` → `payment_service.service.PaymentGatewayUnavailable` (exact, `src/payment_service/service.py:67`)
- `payment_service.service.PaymentService.authorize` → `payment_service.ports.PaymentGateway.request_authorization` (exact, `src/payment_service/service.py:52`)
- `payment_service.service.PaymentService.authorize` → `payment_service.ports.PaymentGateway.request_authorization` (exact, `src/payment_service/service.py:60`)
- `payment_service.service.PaymentService.authorize` → `payment_service.ports.PaymentRepository.find_by_key` (exact, `src/payment_service/service.py:47`)
- `payment_service.service.PaymentService.authorize` → `payment_service.ports.PaymentRepository.save` (exact, `src/payment_service/service.py:77`)

## Test generation guidance

- Query the exact target symbol before writing a test.
- Treat branch inventory as candidate cases, not proof of coverage.
- Check curated domain rules and the current implementation before asserting behavior.
- Prefer ports and protocols as mock boundaries.
