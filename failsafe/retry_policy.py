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

from datetime import timedelta
import random


class Backoff:
    """
    Base class to determine how long to wait between calls.
    """
    def __init__(self, delay, max_delay, factor=2, jitter=False):
        if not isinstance(delay, timedelta):
            raise ValueError("`delay` must be an instance of `datetime.timedelta`.")
        if not isinstance(max_delay, timedelta):
            raise ValueError("`max_delay` must be an instance of `datetime.timedelta`.")

        self.delay = delay
        self.max_delay = max_delay
        self.factor = factor
        self.jitter = jitter

    def for_attempt(self, attempt):
        """
        Subclasses should override this method to return the amount of time to wait
        before the next attempt, in seconds.

        :param attempt: Specifies how many attempts have already happened.
        :return:
        """

        if attempt < 1:
            raise ValueError("`attempt` must be a positive integer.")

        delay = self.delay.total_seconds()
        duration = float(delay * pow(self.factor, attempt - 1))
        if self.jitter is True:
            duration = random.uniform(0.0, duration)
        max_delay = self.max_delay.total_seconds()

        if duration > max_delay:
            return max_delay

        return duration


class Delay(Backoff):
    """
    A special case of ``Backoff` where the wait between calls is constant.
    """
    def __init__(self, delay):
        super(Delay, self).__init__(delay, delay, factor=1, jitter=False)


class RetryPolicy:
    """
    Model to store the number of allowed retries, the allowed retriable exceptions
    and the exceptions that should abort the failsafe run.
    """

    def __init__(self, allowed_retries=3, retriable_exceptions=None, abortable_exceptions=None,
                 backoff=None):
        """
        Constructs RetryPolicy.

        :param allowed_retries: number indicating how many retries can be performed. 0 means no retries.
        :param retriable_exceptions: list of exception types indicating which exceptions can cause a retry. If None
            every exception is considered retriable
        :param abortable_exceptions: list of exception types indicating which exceptions should abort failsafe run
            immediately and be propagated out of failsafe. If None, no exception is considered abortable.
        :param backoff: specification of the wait time between retries. Should be implementation of the Backoff class.
            If None, retries will be executed immediately.
        """
        self.allowed_retries = allowed_retries
        self.retriable_exceptions = retriable_exceptions
        self.abortable_exceptions = abortable_exceptions

        if backoff is None:
            backoff = Delay(timedelta(0))
        self.backoff = backoff

    def should_retry(self, context, exception):
        """
        Returns a boolean indicating if a retry should be performed taking into
        account the number of attempts already performed and the retriable_exceptions.

        :param context: :class:`failsafe.failsafe.Context`.
        :param exception: Exception which caused failure to be considered
            retriable or not raised during the execution.
        """
        should_retry = context.attempts <= self.allowed_retries and self._is_retriable_exception(exception)

        if should_retry:
            wait_for = self.backoff.for_attempt(context.attempts)
            return True, wait_for

        return False, None

    def should_abort(self, exception):
        """
        Returns a boolean indicating whether failsafe run should be aborted and exception propagated
        outside the failsafe.

        :param exception: Exception which caused failure to be considered
            abortable or not during the execution.
        """
        if self.abortable_exceptions is None:
            return False

        return any(isinstance(exception, e) for e in self.abortable_exceptions)

    def _is_retriable_exception(self, exception):
        if self.retriable_exceptions is None:
            return True

        return any(isinstance(exception, e) for e in self.retriable_exceptions)
