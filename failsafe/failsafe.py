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


import asyncio
import logging

from failsafe.circuit_breaker import AlwaysClosedCircuitBreaker
from failsafe.retry_policy import RetryPolicy

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

    def __init__(self, retry_policy=None, circuit_breaker=None):
        if retry_policy is None:
            retry_policy = RetryPolicy(allowed_retries=0)
        self.retry_policy = retry_policy

        if circuit_breaker is None:
            circuit_breaker = AlwaysClosedCircuitBreaker()
        self.circuit_breaker = circuit_breaker

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
                if recent_exception is None:
                    raise CircuitOpen()
                else:
                    raise CircuitOpen() from recent_exception
            try:
                context.attempts += 1
                result = await callable()
                self.circuit_breaker.record_success()
                return result

            except Exception as e:
                if self.retry_policy.should_abort(e):
                    logger.debug("Aborting Failsafe, exception {}".format(type(e).__name__))
                    raise
                recent_exception = e
                context.errors += 1
                retry, wait_for = self.retry_policy.should_retry(context, e)
                self.circuit_breaker.record_failure()

                if retry:
                    if wait_for:
                        logger.debug("Waiting {}".format(wait_for))
                        await asyncio.sleep(wait_for)
                    logger.debug("Retrying call")

        raise RetriesExhausted() from recent_exception
