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

import pytest
from failsafe.failsafe import Context
from failsafe.retry_policy import RetryPolicy, Delay, Backoff

from datetime import timedelta
import random


class TestRetryPolicy:

    def test_should_retry_when_attempts_is_less_then_limit(self):
        retry_policy = RetryPolicy(allowed_retries=3)

        context = Context()
        context.attempts = 3

        assert retry_policy.should_retry(context, Exception()) == (True, 0)

    def test_should_not_retry_when_there_were_too_many_attempts(self):
        retry_policy = RetryPolicy(allowed_retries=3)

        context = Context()
        context.attempts = 4

        assert retry_policy.should_retry(context, Exception()) == (False, None)

    def test_should_not_retry_when_exception_is_not_retriable(self):
        retry_policy = RetryPolicy(allowed_retries=3, retriable_exceptions=[BufferError])

        context = Context()
        context.attempts = 3

        assert retry_policy.should_retry(context, ArithmeticError()) == (False, None)

    def test_should_retry_when_exception_is_retriable(self):
        retry_policy = RetryPolicy(allowed_retries=3, retriable_exceptions=[BufferError])

        context = Context()
        context.attempts = 3

        assert retry_policy.should_retry(context, BufferError()) == (True, 0)

    def test_should_not_retry_when_exception_is_retriable_but_there_were_too_many_attempts(self):
        retry_policy = RetryPolicy(allowed_retries=3, retriable_exceptions=[BufferError])

        context = Context()
        context.attempts = 4

        assert retry_policy.should_retry(context, BufferError()) == (False, None)

    def test_should_retry_with_more_that_one_exception_type(self):
        retry_policy = RetryPolicy(allowed_retries=3, retriable_exceptions=[BufferError, ValueError])

        context = Context()
        context.attempts = 3

        assert retry_policy.should_retry(context, BufferError()) == (True, 0)
        assert retry_policy.should_retry(context, ValueError()) == (True, 0)

    def test_should_abort(self):
        raise_policy = RetryPolicy(abortable_exceptions=[AttributeError])
        assert raise_policy.should_abort(BufferError()) is False
        assert raise_policy.should_abort(AttributeError()) is True

    def test_delay(self):
        with pytest.raises(ValueError):
            Delay(1)

        delay = Delay(timedelta(seconds=1))
        assert delay.for_attempt(1) == 1.0
        assert delay.for_attempt(2) == 1.0
        assert delay.for_attempt(3) == 1.0

    def test_backoff(self):
        with pytest.raises(ValueError):
            Backoff(1, 5)

        with pytest.raises(ValueError):
            Backoff(timedelta(seconds=1), 5)

        with pytest.raises(ValueError):
            Backoff(1, timedelta(seconds=5))

        backoff = Backoff(timedelta(seconds=1), timedelta(seconds=5))

        with pytest.raises(ValueError):
            backoff.for_attempt(0)

        assert backoff.for_attempt(1) == 1.0
        assert backoff.for_attempt(2) == 2.0
        assert backoff.for_attempt(3) == 4.0
        assert backoff.for_attempt(4) == 5.0

    def test_backoff_jitter(self):
        random.seed(123)
        backoff = Backoff(timedelta(seconds=1), timedelta(seconds=5), jitter=True)
        assert round(backoff.for_attempt(1), 3) == 0.052
        assert round(backoff.for_attempt(2), 3) == 0.174
        assert round(backoff.for_attempt(3), 3) == 1.629
        assert round(backoff.for_attempt(4), 3) == 0.862
        assert round(backoff.for_attempt(5), 3) == 5.0

        for i in range(1, 5):
            assert round(backoff.for_attempt(i), 3) <= 5.0
