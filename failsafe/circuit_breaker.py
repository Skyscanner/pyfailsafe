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

    def __init__(self, maximum_failures=2, reset_timeout_seconds=60):
        self.maximum_failures = maximum_failures
        self.reset_timeout_seconds = reset_timeout_seconds

        self.state = ClosedState(self)
        self.reason = None

    def allows_execution(self):
        return self.state.allows_execution()

    def record_success(self):
        self.state.record_success()
        logger.debug("Success recorded")

    def record_failure(self, exception):
        self.state.record_failure(exception)
        logger.debug("Failure recorded")

    def open(self, exception):
        self.state = OpenState(self)
        self.reason = exception
        logger.debug("Opened")

    def close(self):
        self.state = ClosedState(self)
        self.reason = None
        logger.debug("Closed")

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

    def record_failure(self, exception):
        self.current_failures += 1
        if self.current_failures >= self.circuit_breaker.maximum_failures:
            self.circuit_breaker.open(exception)

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

    def record_failure(self, exception):
        pass
