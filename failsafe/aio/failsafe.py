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
import time
from contextlib import contextmanager, asynccontextmanager

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
        self.recent_exception = None


class BaseFailsafe:
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


class _Run:
    def __init__(self, failsafe):
        self.failsafe = failsafe
        self.retry = True
        self.wait_for = 0
        self.context = Context()

    @contextmanager
    def _run(self):
        self._maybe_open_circuit()
        self._on_about_to_run()
        try:
            yield
        except Exception as e:
            self._maybe_abort(e)
            self._on_error(e)
        else:
            self._on_succes()

    @contextmanager
    def _wait_before_retry(self):
        if self.retry and self.wait_for:
            self._on_about_to_wait()

        yield self.wait_for

        if self.retry:
            self._on_about_to_retry()

    async def arun(self, coroutine, *args, **kwargs):
        while self.retry:
            with self._run():
                return await coroutine(*args, **kwargs)

            with self._wait_before_retry() as wait_seconds:
                if wait_seconds:
                    await asyncio.sleep(wait_seconds)

        self._on_retries_exceeded()

    def run(self, callable, *args, **kwargs):
        while self.retry:
            with self._run():
                return callable(*args, **kwargs)

            with self._wait_before_retry() as wait_seconds:
                if wait_seconds:
                    time.sleep(wait_seconds)

        self._on_retries_exceeded()

    def _on_about_to_wait(self):
        logger.debug("Waiting {}".format(self.wait_for))

    def _on_about_to_retry(self):
        logger.debug("Retrying call")
        _safe_call(self.failsafe.retry_policy.on_retry)

    def _on_retries_exceeded(self):
        _safe_call(self.failsafe.retry_policy.on_retries_exceeded)
        raise RetriesExhausted() from self.context.recent_exception

    def _on_error(self, exception):
        self.context.recent_exception = exception
        self.context.errors += 1
        self.retry, self.wait_for = self.failsafe.retry_policy.should_retry(self.context)
        self.failsafe.circuit_breaker.record_failure()
        _safe_call(self.failsafe.retry_policy.on_failed_attempt)

    def _maybe_abort(self, exception):
        if self.failsafe.retry_policy.should_abort(exception):
            logger.debug("Aborting Failsafe, exception {}".format(type(exception).__name__))
            _safe_call(self.failsafe.retry_policy.on_abort)
            raise

    def _on_about_to_run(self):
        self.context.attempts += 1
        self.context.recent_exception = None

    def _on_succes(self):
        self.failsafe.circuit_breaker.record_success()

    def _maybe_open_circuit(self):
        if not self.failsafe.circuit_breaker.allows_execution():
            logger.debug("Circuit open, stopping execution")
            if self.context.recent_exception is None:
                raise CircuitOpen()
            else:
                raise CircuitOpen() from self.context.recent_exception


class Failsafe(BaseFailsafe):
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
        return await _Run(self).arun(coroutine, *args, **kwargs)


class SyncFailsafe(BaseFailsafe):
    def run(self, callable, *args, **kwargs):
        """
        Calls the given callable according to the retry_policy and the circuit_breaker
        specified in the instance.

        :param coroutine: callable to call.
        :param *args:    The original positional arguments of the callable to call (<callable>).
        :param **kwargs: The original keyword arguments of the callable to call (<callable>).

        :raises: RetriesExhausted when the retry policy attempts has been reached.
        :raises: CircuitOpen when the circuit_breaker policy has reached the
            maximum allowed number of failures
        """
        return _Run(self).run(callable, *args, **kwargs)
