# Generated test-impact index: `payment_service`

> Static call relationships only. This is not a runtime coverage report.

| Production symbol | Direct test callers | Static branches |
|---|---|---:|
| `payment_service.models.Order` | `test_payment_service.PaymentServiceTest.test_authorizes_and_persists_payment`<br>`test_payment_service.PaymentServiceTest.test_rejects_non_positive_amount_before_dependencies`<br>`test_payment_service.PaymentServiceTest.test_retries_once_then_translates_second_timeout` | 0 |
| `payment_service.models.Payment` | — | 0 |
| `payment_service.models.PaymentStatus` | — | 0 |
| `payment_service.ports.PaymentGateway` | — | 0 |
| `payment_service.ports.PaymentRepository` | — | 0 |
| `payment_service.service.InvalidAmountError` | — | 0 |
| `payment_service.service.PaymentGatewayUnavailable` | — | 0 |
| `payment_service.service.PaymentService` | `test_payment_service.PaymentServiceTest.test_authorizes_and_persists_payment`<br>`test_payment_service.PaymentServiceTest.test_rejects_non_positive_amount_before_dependencies`<br>`test_payment_service.PaymentServiceTest.test_retries_once_then_translates_second_timeout` | 0 |
| `payment_service.ports.PaymentGateway.request_authorization` | — | 0 |
| `payment_service.ports.PaymentRepository.find_by_key` | — | 0 |
| `payment_service.ports.PaymentRepository.save` | — | 0 |
| `payment_service.service.PaymentService.__init__` | — | 0 |
| `payment_service.service.PaymentService.authorize` | `test_payment_service.PaymentServiceTest.test_authorizes_and_persists_payment`<br>`test_payment_service.PaymentServiceTest.test_rejects_non_positive_amount_before_dependencies`<br>`test_payment_service.PaymentServiceTest.test_retries_once_then_translates_second_timeout` | 2 |

## Interpretation

A symbol with a direct test caller may still have untested branches. Use the graph query tool, read the current implementation, and run tests before making coverage claims.
