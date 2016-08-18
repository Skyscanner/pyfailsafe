import time


class CircuitBreaker:

    def __init__(self, maximum_failures=2, reset_timeout_seconds=60):
        self.maximum_failures = maximum_failures
        self.reset_timeout_seconds = reset_timeout_seconds

        self.state = ClosedState(self)

    def allows_execution(self):
        return self.state.allows_execution()

    def record_success(self):
        self.state.record_success()

    def record_failure(self):
        self.state.record_failure()

    def open(self):
        self.state = OpenState(self)

    def close(self):
        self.state = ClosedState(self)

    @property
    def current_state(self):
        return self.state.get_name()


class ClosedState:
    def __init__(self, circuit_breaker):
        self.circuit_breaker = circuit_breaker
        self.current_failures = 0

    def allows_execution(self):
        return True

    def record_success(self):
        self.current_failures = 0

    def record_failure(self):
        self.current_failures += 1
        if self.current_failures >= self.circuit_breaker.maximum_failures:
            self.circuit_breaker.open()

    def get_name(self):
        return 'closed'


class OpenState:
    def __init__(self, circuit_breaker):
        self.circuit_breaker = circuit_breaker
        self.opened_at = time.monotonic()

    def allows_execution(self):
        if time.monotonic() > self.opened_at + self.circuit_breaker.reset_timeout_seconds:
            self.circuit_breaker.close()
            return True

        return False

    def record_success(self):
        pass

    def record_failure(self):
        pass

    def get_name(self):
        return 'open'


class AlwaysClosedCircuitBreaker(CircuitBreaker):
    def __init__(self):
        pass

    def allows_execution(self):
        return True

    def record_success(self):
        pass

    def record_failure(self):
        pass
