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

from failsafe._internal import _safe_call
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

    async def run(self, coroutine, *args, **kwargs):
        """
        Calls the given coroutine according to the retry_policy and the circuit_breaker
        specified in the instance.

        :param coroutine: coroutine to call.
        :param *args:    The original positional arguments of the coroutine to call (<coroutine>).
        :param **kwargs: The original keyword arguments of the coroutine to call (<coroutine>).

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
                result = await coroutine(*args, **kwargs)
                self.circuit_breaker.record_success()
                return result

            except Exception as e:
                if self.retry_policy.should_abort(e):
                    logger.debug("Aborting Failsafe, exception {}".format(type(e).__name__))
                    _safe_call(self.retry_policy.on_abort)
                    raise
                recent_exception = e
                context.errors += 1
                retry, wait_for = self.retry_policy.should_retry(context, e)
                self.circuit_breaker.record_failure()
                _safe_call(self.retry_policy.on_failed_attempt)

                if retry:
                    if wait_for:
                        logger.debug("Waiting {}".format(wait_for))
                        await asyncio.sleep(wait_for)
                    logger.debug("Retrying call")
                    _safe_call(self.retry_policy.on_retry)

        _safe_call(self.retry_policy.on_retries_exceeded)
        raise RetriesExhausted() from recent_exception


class Sync:
    """
    Convenience decorator class to use a `Failsafe` instance from "classic" code (as in not using `async`/`await`
    syntax). Uses `asyncio.run()` (available in python 3.7+) or `asyncio.get_event_loop().run_until_complete()` if
    `asyncio.run()` isn't available.

    Usage:
        ```
        def classic_callable():
            ...

        failsafe = Sync(Failsafe(retry_policy=...))
        failsafe.run(classic_callable)
        ```
    """
    def __init__(self, failsafe):
        self._failsafe = failsafe

    async def _sync_call(self, callable, *args, **kwargs):
        return callable(*args, **kwargs)

    async def _failsafe_run(self, callable, *args, **kwargs):
        return await self._failsafe.run(self._sync_call, callable, *args, **kwargs)

    def run(self, callable, *args, **kwargs):
        """
        Calls the given method according to the retry_policy and the circuit_breaker
        specified in the decorated Failsafe instance.

        :param callable: method to call.
        :param *args:    The original positional arguments of the method to call (<callable>).
        :param **kwargs: The original keyword arguments of the method to call (<callable>).

        :raises: RetriesExhausted when the retry policy attempts has been reached.
        :raises: CircuitOpen when the circuit_breaker policy has reached the
            maximum allowed number of failures
        """
        coroutine = self._failsafe_run(callable, *args, **kwargs)
        if hasattr(asyncio, 'run'):
            return asyncio.run(coroutine)
        else:
            return asyncio.get_event_loop().run_until_complete(coroutine)
