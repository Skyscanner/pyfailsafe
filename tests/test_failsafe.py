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
import unittest
from unittest.mock import MagicMock, Mock, call
import pytest

from failsafe import (
    RetryPolicy, Failsafe, CircuitOpen, CircuitBreaker, RetriesExhausted, Delay,
    Backoff,
)
from datetime import timedelta


loop = asyncio.get_event_loop()


def get_mock_coro(return_value):
    @asyncio.coroutine
    def mock_coro(*args, **kwargs):
        return return_value

    return Mock(wraps=mock_coro)


def create_succeeding_operation():
    async def operation():
        operation.called += 1

    operation.called = 0
    return operation


def create_failing_operation(exception=None):
    async def operation():
        operation.called += 1
        if exception:
            raise exception
        raise SomeRetriableException()

    operation.called = 0
    return operation


def create_aborting_operation():
    async def operation():
        operation.called += 1
        raise SomeAbortableException()

    operation.called = 0
    return operation


class SomeRetriableException(Exception):
    pass


class SomeAbortableException(Exception):
    pass


class TestFailsafe(unittest.TestCase):

    def test_failsafe_on_method_with_arguments(self):
        class Operation:
            async def task_with_arguments(self, x, y=0):
                result = x + y
                return "{0}_{1}".format(self.__class__.__name__, result)

        operation = Operation()
        obtained = loop.run_until_complete(
            Failsafe().run(operation.task_with_arguments, 41, y=1)
        )
        assert obtained == "{0}_42".format(Operation.__name__)

    def test_no_retry(self):
        succeeding_operation = create_succeeding_operation()
        loop.run_until_complete(
            Failsafe().run(succeeding_operation)
        )
        assert succeeding_operation.called == 1

    def test_basic_retry(self):
        succeeding_operation = create_succeeding_operation()
        on_retry_mock = Mock()
        on_abort_mock = Mock()
        on_failed_attempt_mock = Mock()
        on_retries_exceeded_mock = Mock()
        policy = RetryPolicy(on_retry=on_retry_mock, on_abort=on_abort_mock, on_failed_attempt=on_failed_attempt_mock,
                             on_retries_exhausted=on_retries_exceeded_mock)
        loop.run_until_complete(
            Failsafe(retry_policy=policy).run(succeeding_operation)
        )
        assert succeeding_operation.called == 1
        assert not on_retry_mock.called
        assert not on_abort_mock.called
        assert not on_failed_attempt_mock.called
        assert not on_retries_exceeded_mock.called

    def test_retry_once(self):
        failing_operation = create_failing_operation()
        expected_attempts = 2
        retries = 1
        on_retry_mock = Mock()
        on_failed_attempt_mock = Mock()
        policy = RetryPolicy(retries, on_retry=on_retry_mock, on_failed_attempt=on_failed_attempt_mock)
        failsafe = Failsafe(retry_policy=policy)

        assert failing_operation.called == 0

        with pytest.raises(RetriesExhausted):
            loop.run_until_complete(
                failsafe.run(failing_operation)
            )

        assert failing_operation.called == expected_attempts
        assert on_retry_mock.call_count == retries
        assert on_failed_attempt_mock.call_count == expected_attempts

    def test_retry_four_times(self):
        failing_operation = create_failing_operation()
        expected_attempts = 5
        retries = 4
        on_retry_mock = Mock()
        on_failed_attempt_mock = Mock()
        policy = RetryPolicy(retries, on_retry=on_retry_mock, on_failed_attempt=on_failed_attempt_mock)
        failsafe = Failsafe(retry_policy=policy)

        assert failing_operation.called == 0

        with pytest.raises(RetriesExhausted):
            loop.run_until_complete(
                failsafe.run(failing_operation)
            )

        assert failing_operation.called == expected_attempts
        assert on_retry_mock.call_count == retries
        assert on_failed_attempt_mock.call_count == expected_attempts

    def test_retry_on_custom_exception(self):
        failing_operation = create_failing_operation()
        retries = 3
        policy = RetryPolicy(retries, [SomeRetriableException])
        failsafe = Failsafe(retry_policy=policy)

        assert failing_operation.called == 0

        with pytest.raises(RetriesExhausted):
            loop.run_until_complete(
                failsafe.run(failing_operation)
            )

        assert failing_operation.called == retries + 1

    @unittest.mock.patch('asyncio.sleep', get_mock_coro(None))
    def test_delay(self):
        failing_operation = create_failing_operation()
        retries = 3
        delay = Delay(timedelta(seconds=0.2))
        policy = RetryPolicy(retries, [SomeRetriableException], backoff=delay)
        with pytest.raises(RetriesExhausted):
            loop.run_until_complete(
                Failsafe(retry_policy=policy)
                .run(failing_operation)
            )
        assert asyncio.sleep.mock_calls == [
            call(0.2),
            call(0.2),
            call(0.2),
        ]

    @unittest.mock.patch('asyncio.sleep', get_mock_coro(None))
    def test_backoff(self):
        failing_operation = create_failing_operation()
        retries = 3
        backoff = Backoff(timedelta(seconds=0.2), timedelta(seconds=1))
        policy = RetryPolicy(retries, [SomeRetriableException], backoff=backoff)
        Failsafe(retry_policy=policy)
        with pytest.raises(RetriesExhausted):
            loop.run_until_complete(
                Failsafe(retry_policy=policy)
                .run(failing_operation)
            )
        assert asyncio.sleep.mock_calls == [
            call(0.2),
            call(0.4),
            call(0.8),
        ]

    def test_circuit_breaker_with_retries(self):
        failing_operation = create_failing_operation()

        with pytest.raises(CircuitOpen):
            policy = RetryPolicy(5, [SomeRetriableException])
            circuit_breaker = CircuitBreaker(maximum_failures=2)
            loop.run_until_complete(
                Failsafe(retry_policy=policy, circuit_breaker=circuit_breaker)
                .run(failing_operation)
            )
        assert failing_operation.called == 2

    def test_circuit_breaker_circuitopener_raises_circuitopen_with_cause(self):
        original_exception = SomeRetriableException("My Error Message")
        failing_operation = create_failing_operation(original_exception)
        try:
            policy = RetryPolicy(5, [SomeRetriableException])
            circuit_breaker = CircuitBreaker(maximum_failures=2)
            loop.run_until_complete(
                Failsafe(retry_policy=policy, circuit_breaker=circuit_breaker)
                .run(failing_operation)
            )
            raise Exception("Expected CircuitOpen exception")
        except CircuitOpen as e:
            assert e.__cause__ is original_exception

    def test_circuit_breaker_opened_circuit_has_no_cause(self):
        failing_operation = create_failing_operation()
        try:
            policy = RetryPolicy(5, [SomeRetriableException])
            circuit_breaker = CircuitBreaker(maximum_failures=2)
            circuit_breaker.open()

            loop.run_until_complete(
                Failsafe(retry_policy=policy, circuit_breaker=circuit_breaker)
                .run(failing_operation)
            )
            raise Exception("Expected CircuitOpen exception")
        except CircuitOpen as e:
            assert e.__cause__ is None
        assert failing_operation.called == 0

    def test_circuit_breaker_with_abort(self):
        aborting_operation = create_aborting_operation()
        on_abort_mock = Mock()

        policy = RetryPolicy(abortable_exceptions=[SomeAbortableException], on_abort=on_abort_mock)
        circuit_breaker = CircuitBreaker(maximum_failures=2)

        circuit_breaker.record_failure = MagicMock()
        with pytest.raises(SomeAbortableException):
            loop.run_until_complete(
                Failsafe(retry_policy=policy, circuit_breaker=circuit_breaker)
                .run(aborting_operation)
            )
        circuit_breaker.record_failure.assert_not_called()

        assert aborting_operation.called == 1
        assert on_abort_mock.call_count == 1

    def test_safe_abort_event(self):
        aborting_operation = create_aborting_operation()
        on_abort_mock = Mock()
        on_abort_mock.side_effect = Exception("ERROR!")

        policy = RetryPolicy(abortable_exceptions=[SomeAbortableException], on_abort=on_abort_mock)

        with pytest.raises(SomeAbortableException):
            loop.run_until_complete(
                Failsafe(retry_policy=policy)
                .run(aborting_operation)
            )

        assert on_abort_mock.called

    def test_safe_rest_of_events(self):
        retries = 1
        failing_operation = create_failing_operation()
        on_retry_mock = Mock()
        on_retry_mock.side_effect = Exception("ERROR!")
        on_failed_attempt_mock = Mock()
        on_failed_attempt_mock.side_effect = Exception("ERROR!")
        on_retries_exhausted_mock = Mock()
        on_retries_exhausted_mock.side_effect = Exception("ERROR!")
        policy = RetryPolicy(retries, on_retry=on_retry_mock, on_failed_attempt=on_failed_attempt_mock,
                             on_retries_exhausted=on_retries_exhausted_mock)
        failsafe = Failsafe(retry_policy=policy)

        with pytest.raises(RetriesExhausted):
            loop.run_until_complete(
                failsafe.run(failing_operation)
            )

        assert on_retry_mock.called
        assert on_failed_attempt_mock.called
        assert on_retries_exhausted_mock.called
