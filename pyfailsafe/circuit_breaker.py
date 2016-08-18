import time


class CircuitBreaker:
    def __init__(self, maximum_failures=2, reset_timeout_seconds=60):
        self.maximum_failures = maximum_failures
        self.reset_timeout_seconds = reset_timeout_seconds

        self.current_state = ClosedState(self)

    def allows_execution(self):
        return self.current_state.allows_execution()

    def record_success(self):
        self.current_state.record_success()

    def record_failure(self):
        self.current_state.record_failure()

    def open(self):
        self.current_state = OpenState(self)

    def close(self):
        self.current_state = ClosedState(self)


class OpenState:
    def __init__(self, circuit_breaker):
        self.circuit_breaker = circuit_breaker
        self.opened_at = time.monotonic()

    def allows_execution(self):
        if self.opened_at + self.circuit_breaker.reset_timeout_seconds > time.monotonic():
            self.circuit_breaker.close()
            return True

        return False

    def record_success(self):
        pass

    def record_failure(self):
        pass


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


class AlwaysClosedCircuitBreaker(CircuitBreaker):
    def __init__(self):
        pass

    def allows_execution(self):
        return True

    def record_success(self):
        pass

    def record_failure(self):
        pass
