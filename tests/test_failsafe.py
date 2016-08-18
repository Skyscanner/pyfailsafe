import asyncio
import unittest

import pytest

from failsafe import RetryPolicy, FailSafe, CircuitOpen, CircuitBreaker, RetriesExhausted


class SomeRetriableException(Exception):
    pass


async def successful_operation():
    return 1

async def failing_operation():
    raise SomeRetriableException()


loop = asyncio.get_event_loop()


class TestFailSafe(unittest.TestCase):

    def test_no_retry(self):
        loop.run_until_complete(
            FailSafe().run(successful_operation)
        )

    def test_basic_retry(self):
        policy = RetryPolicy()
        loop.run_until_complete(
            FailSafe(retry_policy=policy).run(successful_operation)
        )

    def test_retry_once(self):
        expected_attempts = 2
        retries = 1
        policy = RetryPolicy(retries)
        failsafe = FailSafe(retry_policy=policy)
        assert failsafe.context.attempts == 0
        with pytest.raises(RetriesExhausted):
            loop.run_until_complete(
                failsafe.run(failing_operation)
            )

        assert failsafe.context.attempts == expected_attempts

    def test_retry_four_times(self):
        expected_attempts = 5
        retries = 4
        policy = RetryPolicy(retries)
        failsafe = FailSafe(retry_policy=policy)
        assert failsafe.context.attempts == 0

        with pytest.raises(RetriesExhausted):
            loop.run_until_complete(
                failsafe.run(failing_operation)
            )

        assert failsafe.context.attempts == expected_attempts

    def test_retry_on_custom_exception(self):
        retries = 3
        policy = RetryPolicy(retries, SomeRetriableException)
        failsafe = FailSafe(retry_policy=policy)
        assert failsafe.context.attempts == 0

        with pytest.raises(RetriesExhausted):
            loop.run_until_complete(
                failsafe.run(failing_operation)
            )

        assert failsafe.context.attempts == retries + 1

    def test_circuit_breaker(self):
        with pytest.raises(CircuitOpen):
            policy = RetryPolicy(5, SomeRetriableException)
            circuit_breaker = CircuitBreaker(maximum_failures=2)
            loop.run_until_complete(
                FailSafe(retry_policy=policy)
                .run(failing_operation, circuit_breaker)
            )
