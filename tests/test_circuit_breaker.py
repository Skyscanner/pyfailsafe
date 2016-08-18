from unittest.mock import patch

from failsafe.circuit_breaker import CircuitBreaker


class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        circuit_breaker = CircuitBreaker()
        assert circuit_breaker.current_state == 'closed'

    def test_closed_circuit_allows_execution(self):
        circuit_breaker = CircuitBreaker()
        assert circuit_breaker.current_state == 'closed'
        assert circuit_breaker.allows_execution() is True

    def test_open_circuit_does_not_allow_execution(self):
        circuit_breaker = CircuitBreaker(maximum_failures=1)
        circuit_breaker.record_failure()
        assert circuit_breaker.current_state == 'open'
        assert circuit_breaker.allows_execution() is False

    def test_circut_stays_closed_after_less_failures_then_limit(self):
        circuit_breaker = CircuitBreaker(maximum_failures=3)
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()

        assert circuit_breaker.current_state == 'closed'

    def test_circut_is_opened_after_failures(self):
        circuit_breaker = CircuitBreaker(maximum_failures=3)
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()

        assert circuit_breaker.current_state == 'open'

    def test_circut_success_resets_failures_counter(self):
        circuit_breaker = CircuitBreaker(maximum_failures=3)
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        circuit_breaker.record_success()
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()

        assert circuit_breaker.current_state == 'closed'

    @patch('time.monotonic')
    def test_circuit_closes_again_after_timeout(self, monotonic_mock):
        circuit_breaker = CircuitBreaker(maximum_failures=1, reset_timeout_seconds=20)

        assert circuit_breaker.allows_execution() is True
        assert circuit_breaker.current_state == 'closed'

        monotonic_mock.return_value = 100

        circuit_breaker.record_failure()

        assert circuit_breaker.allows_execution() is False
        assert circuit_breaker.current_state == 'open'

        monotonic_mock.return_value = 130

        assert circuit_breaker.allows_execution() is True
        assert circuit_breaker.current_state == 'closed'
