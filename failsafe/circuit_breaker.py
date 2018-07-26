# Copyright 2016 Skyscanner Limited.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import logging

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    CircuitBreaker implements a way to temporally disable the execution to
    prevent an overload of the system. By default, a maximum of 2 failures are
    allowed before considering the circuit as open for a period of 60 seconds.
    Additionally, while transitioning from open to closed, it will allow for
    a maximum of n * `half_open_ratio requests` to go through and probe the
    underlying system.

    The initial state of the CircuitBreaker is closed.
    """

    def __init__(self, maximum_failures=2, reset_timeout_seconds=60, half_open_ratio=0.1):
        self.maximum_failures = maximum_failures
        self.reset_timeout_seconds = reset_timeout_seconds
        self.half_open_ratio = half_open_ratio

        self.state = _ClosedState(self)

    def allows_execution(self):
        """
        Returns a boolean indicating if the execution is allowed or not
        depending on the state of the CircuitBreaker
        """
        return self.state.allows_execution()

    def record_success(self):
        """
        Records an execution success.

        Should be called when the operation protected by circuit breaker succeeded.
        This will reset counter of consecutive failures. Does nothing if circuit breaker is open.
        """
        self.state.record_success()
        logger.debug("Success recorded")

    def record_failure(self):
        """
        Records an execution failure.

        Should be called when the operation protected by circuit breaker failed.
        If the number of consecutive failures has reached the allowed number of failures,
        changes the state of the CircuitBreaker to open meaning that `allows_execution` will be
        returning false for the configured timeout. Does nothing if circuit breaker is already open.
        """
        self.state.record_failure()
        logger.debug("Failure recorded")

    def open(self):
        """
        Sets the state of the CircuitBreaker to open
        """
        self.state = _OpenState(self)
        logger.debug("Opened")

    def half_open(self):
        """
        Sets the state of the CircuitBreaker to half open
        """
        self.state = _HalfOpenState(self, self.half_open_ratio)
        logger.debug("Half opened")

    def close(self):
        """
        Sets the state of the CircuitBreaker to closed
        """
        self.state = _ClosedState(self)
        logger.debug("Closed")

    @property
    def current_state(self):
        """
        Get the current state of the CircuitBreaker

        :returns: string `open` or `closed`
        """
        return self.state.get_name()


class _ClosedState:
    """
    A status class representing the closed state of a CircuitBreaker.
    """

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


class _OpenState:
    """
    A status class representing the open state of a CircuitBreaker
    """

    def __init__(self, circuit_breaker):
        self.circuit_breaker = circuit_breaker
        self.opened_at = time.monotonic()

    def allows_execution(self):
        if time.monotonic() > self.opened_at + self.circuit_breaker.reset_timeout_seconds:
            self.circuit_breaker.half_open()
            return True

        return False

    def record_success(self):
        pass

    def record_failure(self):
        pass

    def get_name(self):
        return 'open'


class _HalfOpenState:
    """
    A status class representing the half open state of a CircuitBreaker. The half-open state
    allows for up to n * `half_open_ratio` requests to go through in order to check whether the
    underlying system has recovered or not. The first request that finishes successfully will
    close the circuit - or open it back if it fails instead.
    """

    def __init__(self, circuit_breaker, half_open_ratio):
        self.circuit_breaker = circuit_breaker
        self.attempts = 0
        self.half_open_ratio = half_open_ratio

    def allows_execution(self):
        self.attempts += 1
        if self.attempts % 100 < 100 * self.half_open_ratio:
            return True
        return False

    def record_success(self):
        self.circuit_breaker.close()

    def record_failure(self):
        self.circuit_breaker.open()

    def get_name(self):
        return 'half-open'


class AlwaysClosedCircuitBreaker(CircuitBreaker):
    """
    A CircuitBreaker which is always closed allowing all executions.
    """

    def __init__(self):
        pass

    def allows_execution(self):
        return True

    def record_success(self):
        pass

    def record_failure(self):
        pass
