import asyncio
import aiohttp
import unittest

from failsafe import RetryPolicy, FailSafe, CircuitOpen, CircuitBreaker, RetriesExhausted


class SomeRetriableException(Exception):
    pass


async def get_coroutine(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            # print(resp.status)
            if resp.status != 200:
                raise SomeRetriableException()
            return await resp.json()


loop = asyncio.get_event_loop()

url = 'http://httpbin.org/get'
broken_url = 'http://httpbin.org/getbrooooken'


class TestFailSafe(unittest.TestCase):

    def test_no_retry(self):
        try:
            loop.run_until_complete(
                FailSafe().run(lambda: get_coroutine(url))
            )
        except RetriesExhausted:
            pass

    def test_basic_retry(self):
        try:
            policy = RetryPolicy()
            loop.run_until_complete(
                FailSafe(retry_policy=policy).run(lambda: get_coroutine(url))
            )
        except RetriesExhausted:
            pass

    def test_retry_once(self):
        expected_attempts = 2
        retries = 1
        policy = RetryPolicy(retries)
        failsafe = FailSafe(retry_policy=policy)
        assert failsafe.context.attempts == 0
        try:
            loop.run_until_complete(
                failsafe.run(lambda: get_coroutine(broken_url))
            )
        except RetriesExhausted:
            pass

        assert failsafe.context.attempts == expected_attempts

    def test_retry_four_times(self):
        expected_attempts = 5
        retries = 4
        policy = RetryPolicy(retries)
        failsafe = FailSafe(retry_policy=policy)
        assert failsafe.context.attempts == 0

        try:
            loop.run_until_complete(
                failsafe.run(lambda: get_coroutine(broken_url))
            )
        except RetriesExhausted:
            pass

        assert failsafe.context.attempts == expected_attempts

    def test_retry_on_custom_exception(self):
        retries = 3
        policy = RetryPolicy(retries, SomeRetriableException)
        failsafe = FailSafe(retry_policy=policy)
        assert failsafe.context.attempts == 0

        try:
            loop.run_until_complete(
                failsafe.run(lambda: get_coroutine(broken_url))
            )
        except RetriesExhausted:
            pass

        assert failsafe.context.attempts == retries + 1

    def test_circuit_breaker(self):
        try:
            policy = RetryPolicy(5, SomeRetriableException)
            circuit_breaker = CircuitBreaker()
            loop.run_until_complete(
                FailSafe(retry_policy=policy)
                .run(lambda: get_coroutine(broken_url), circuit_breaker)
            )
        except CircuitOpen:
            pass

        assert len(circuit_breaker.failures) == 1
