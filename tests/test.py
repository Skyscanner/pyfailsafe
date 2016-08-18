import asyncio
import aiohttp

from pyfailsafe import RetryPolicy, TryAgain, CircuitOpen, CircuitBreaker, NoMoreFallbacks


class SomeRetriableException(Exception):
    pass


async def get_events(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            # print(resp.status)
            if resp.status != 200:
                raise SomeRetriableException()
            return await resp.json()


loop = asyncio.get_event_loop()

url = 'http://httpbin.org/get'
broken_url = 'http://httpbin.org/getbrooooken'


class TestTryAgain:

    def test_no_retry(self):
        try:
            loop.run_until_complete(
                TryAgain().run(lambda: get_events(url))
            )
        except NoMoreFallbacks:
            pass

    def test_basic_retry(self):
        try:
            policy = RetryPolicy()
            loop.run_until_complete(
                TryAgain().with_retry_policy(policy).run(lambda: get_events(url))
            )
        except NoMoreFallbacks:
            pass

    def test_retry_once(self):
        expected_attempts = 2
        retries = 1
        policy = RetryPolicy(retries)
        tryagain = TryAgain()
        assert tryagain.context.attempts == 0
        try:
            loop.run_until_complete(
                tryagain.with_retry_policy(policy).run(lambda: get_events(broken_url))
            )
        except NoMoreFallbacks:
            pass

        assert tryagain.context.attempts == expected_attempts

    def test_retry_four_times(self):
        expected_attempts = 5
        retries = 4
        policy = RetryPolicy(retries)
        tryagain = TryAgain()
        assert tryagain.context.attempts == 0

        try:
            loop.run_until_complete(
                tryagain.with_retry_policy(policy).run(lambda: get_events(broken_url))
            )
        except NoMoreFallbacks:
            pass

        assert tryagain.context.attempts == expected_attempts

    def test_retry_on_custom_exception(self):
        retries = 3
        policy = RetryPolicy(retries, SomeRetriableException)
        tryagain = TryAgain()
        assert tryagain.context.attempts == 0

        try:
            loop.run_until_complete(
                tryagain.with_retry_policy(policy).run(lambda: get_events(broken_url))
            )
        except NoMoreFallbacks:
            pass

        assert tryagain.context.attempts == retries + 1

    def test_fallback(self):
        policy = RetryPolicy(1, SomeRetriableException)
        fallback = lambda: get_events('http://httpbin.org/get')
        loop.run_until_complete(
            TryAgain().with_retry_policy(policy).with_fallback(fallback).run(lambda: get_events(broken_url))
        )

    def test_circuit_breaker(self):
        try:
            policy = RetryPolicy(5, SomeRetriableException)
            circuit_breaker = CircuitBreaker()
            loop.run_until_complete(
                TryAgain()
                    .with_retry_policy(policy)
                    .run(lambda: get_events('http://httpbin.org/getbrooooken'), circuit_breaker)
            )
        except CircuitOpen:
            pass

        assert len(circuit_breaker.failures) == 1

    def test_fallback_circuit_breaker(self):
        try:
            policy = RetryPolicy(5, SomeRetriableException)
            fallback_circuit_breaker = CircuitBreaker()
            fallback = lambda: get_events(broken_url)
            loop.run_until_complete(
                TryAgain()
                    .with_fallback(fallback, fallback_circuit_breaker)
                    .with_retry_policy(policy)
                    .run(lambda: get_events(broken_url))
            )
        except CircuitOpen:
            pass

        assert len(fallback_circuit_breaker.failures) == 1

    def test_both_circuit_breakers(self):
        retries = 5
        policy = RetryPolicy(retries, SomeRetriableException)
        threshold = 4
        circuit_breaker = CircuitBreaker(threshold=threshold)
        fallback_circuit_breaker = CircuitBreaker()
        fallback = lambda: get_events(broken_url)
        try:
            loop.run_until_complete(
                TryAgain()
                    .with_fallback(fallback, fallback_circuit_breaker)
                    .with_retry_policy(policy)
                    .run(lambda: get_events(broken_url), circuit_breaker)
            )
        except CircuitOpen:
            pass

        assert len(circuit_breaker.failures) == threshold + 1
        assert len(fallback_circuit_breaker.failures) == 1
