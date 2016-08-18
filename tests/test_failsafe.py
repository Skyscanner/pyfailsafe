import asyncio
import unittest

import pytest

from failsafe import RetryPolicy, Failsafe, CircuitOpen, CircuitBreaker, RetriesExhausted


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


class SomeRetriableException(Exception):
    pass


class TestFailSafe(unittest.TestCase):

    def test_no_retry(self):
        succeeding_operation = create_succeeding_operation()
        loop.run_until_complete(
            Failsafe().run(succeeding_operation)
        )

    def test_basic_retry(self):
        succeeding_operation = create_succeeding_operation()
        policy = RetryPolicy()
        loop.run_until_complete(
            Failsafe(retry_policy=policy).run(succeeding_operation)
        )

    def test_retry_once(self):
        failing_operation = create_failing_operation()
        expected_attempts = 2
        retries = 1
        policy = RetryPolicy(retries)
        failsafe = Failsafe(retry_policy=policy)

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
        policy = RetryPolicy(retries)
        failsafe = Failsafe(retry_policy=policy)

        assert failing_operation.called == 0

        with pytest.raises(RetriesExhausted):
            loop.run_until_complete(
                failsafe.run(failing_operation)
            )

        assert failing_operation.called == expected_attempts

    def test_retry_on_custom_exception(self):
        failing_operation = create_failing_operation()
        retries = 3
        policy = RetryPolicy(retries, SomeRetriableException)
        failsafe = Failsafe(retry_policy=policy)

        assert failing_operation.called == 0

        with pytest.raises(RetriesExhausted):
            loop.run_until_complete(
                failsafe.run(failing_operation)
            )

        assert failing_operation.called == retries + 1

    def test_circuit_breaker(self):
        failing_operation = create_failing_operation()

        with pytest.raises(CircuitOpen):
            policy = RetryPolicy(5, SomeRetriableException)
            circuit_breaker = CircuitBreaker(maximum_failures=2)
            loop.run_until_complete(
                Failsafe(retry_policy=policy, circuit_breaker=circuit_breaker)
                .run(failing_operation)
            )

        assert failing_operation.called == 2
