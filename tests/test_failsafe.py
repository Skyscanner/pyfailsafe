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

import pytest

from failsafe import ExceptionHandlingPolicy, Failsafe, CircuitOpen, CircuitBreaker, RetriesExhausted


loop = asyncio.get_event_loop()


def create_succeeding_operation():
    async def operation():
        operation.called += 1

    operation.called = 0
    return operation


def create_failing_operation():
    async def operation():
        operation.called += 1
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

    def test_no_retry(self):
        succeeding_operation = create_succeeding_operation()
        loop.run_until_complete(
            Failsafe().run(succeeding_operation)
        )

    def test_basic_retry(self):
        succeeding_operation = create_succeeding_operation()
        policy = ExceptionHandlingPolicy()
        loop.run_until_complete(
            Failsafe(exception_handling_policy=policy).run(succeeding_operation)
        )

    def test_retry_once(self):
        failing_operation = create_failing_operation()
        expected_attempts = 2
        retries = 1
        policy = ExceptionHandlingPolicy(retries)
        failsafe = Failsafe(exception_handling_policy=policy)

        assert failing_operation.called == 0

        with pytest.raises(RetriesExhausted):
            loop.run_until_complete(
                failsafe.run(failing_operation)
            )

        assert failing_operation.called == expected_attempts

    def test_retry_four_times(self):
        failing_operation = create_failing_operation()
        expected_attempts = 5
        retries = 4
        policy = ExceptionHandlingPolicy(retries)
        failsafe = Failsafe(exception_handling_policy=policy)

        assert failing_operation.called == 0

        with pytest.raises(RetriesExhausted):
            loop.run_until_complete(
                failsafe.run(failing_operation)
            )

        assert failing_operation.called == expected_attempts

    def test_retry_on_custom_exception(self):
        failing_operation = create_failing_operation()
        retries = 3
        policy = ExceptionHandlingPolicy(retries, [SomeRetriableException])
        failsafe = Failsafe(exception_handling_policy=policy)

        assert failing_operation.called == 0

        with pytest.raises(RetriesExhausted):
            loop.run_until_complete(
                failsafe.run(failing_operation)
            )

        assert failing_operation.called == retries + 1

    def test_circuit_breaker_with_retries(self):
        failing_operation = create_failing_operation()

        with pytest.raises(CircuitOpen):
            policy = ExceptionHandlingPolicy(5, [SomeRetriableException])
            circuit_breaker = CircuitBreaker(maximum_failures=2)
            loop.run_until_complete(
                Failsafe(exception_handling_policy=policy, circuit_breaker=circuit_breaker)
                .run(failing_operation)
            )

        assert failing_operation.called == 2

    def test_circuit_breaker_with_abort(self):
        aborting_operation = create_aborting_operation()

        policy = ExceptionHandlingPolicy(abortable_exceptions=[SomeAbortableException])
        circuit_breaker = CircuitBreaker(maximum_failures=2)
        with pytest.raises(SomeAbortableException):
            loop.run_until_complete(
                Failsafe(exception_handling_policy=policy, circuit_breaker=circuit_breaker)
                .run(aborting_operation)
            )

        assert aborting_operation.called == 1
