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

    def __init__(self, retry_policy=None, circuit_breaker=None):
        self.retry_policy = retry_policy or RetryPolicy(0)
        self.circuit_breaker = circuit_breaker or AlwaysClosedCircuitBreaker()

    async def run(self, callable):
        recent_exception = None
        retry = True
        context = Context()

        while retry:
            if not self.circuit_breaker.allows_execution():
                logger.debug("Circuit open, stopping execution")
                raise CircuitOpen() from self.circuit_breaker.reason
            try:
                context.attempts += 1
                result = await callable()
                self.circuit_breaker.record_success()
                return result

            except Exception as e:
                context.errors += 1
                recent_exception = e
                retry = self.retry_policy.should_retry(context, e)
                self.circuit_breaker.record_failure(e)

                if retry:
                    logger.debug("Retrying call")

        raise RetriesExhausted() from recent_exception
