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

import logging

from failsafe.circuit_breaker import AlwaysClosedCircuitBreaker
from failsafe.retry_policy import RetryPolicy
from failsafe.raise_policy import RaisePolicy

logger = logging.getLogger(__name__)


class FailsafeError(Exception):
    pass


class CircuitOpen(FailsafeError):
    pass


class RetriesExhausted(FailsafeError):
    pass


class Context(object):

    def __init__(self):
        self.attempts = 0
        self.errors = 0


class Failsafe:
    """
    Failsafe is used to wrap a method call with a retry policy and/or a circuit breaker.
    By default, the number of retries of the retry policy is 0 so no retries will be allowed
    and the circuit breaker is always closed allowing all calls.
    """

    def __init__(self, retry_policy=None, circuit_breaker=None, raise_policy=None):
        self.retry_policy = retry_policy or RetryPolicy(0)
        self.circuit_breaker = circuit_breaker or AlwaysClosedCircuitBreaker()
        self.raise_policy = raise_policy or RaisePolicy([])

    async def run(self, callable):
        """
        Calls the callable method according to the retry_policy and the circuit_breaker
        specified in the instance.

        :param callable: method to call.
        :raises: RetriesExhausted when the retry policy attempts has been reached.
        :raises: CircuitOpen when the circuit_breaker policy has reached the
            maximum allowed number of failures
        """
        recent_exception = None
        retry = True
        context = Context()

        while retry:
            if not self.circuit_breaker.allows_execution():
                logger.debug("Circuit open, stopping execution")
                raise CircuitOpen()
            try:
                context.attempts += 1
                result = await callable()
                self.circuit_breaker.record_success()
                return result

            except Exception as e:
                context.errors += 1
                recent_exception = e
                retry = self.retry_policy.should_retry(context, e)
                if self.raise_policy.should_raise(e):
                    raise
                self.circuit_breaker.record_failure()

                if retry:
                    logger.debug("Retrying call")

        raise RetriesExhausted() from recent_exception
