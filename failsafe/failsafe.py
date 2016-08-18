from collections import OrderedDict
from urllib.parse import urljoin
import logging

from failsafe.circuit_breaker import AlwaysClosedCircuitBreaker
from failsafe.retry_policy import RetryPolicy
from failsafe.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class AsyncHttpFailsafe:
    def __init__(self, base_urls=None, allowed_retries=4, maximum_failures=2):
        policy = RetryPolicy(allowed_retries=allowed_retries)
        self.failsafe_list = OrderedDict()
        for url in base_urls:
            circuit_breaker = CircuitBreaker(maximum_failures=maximum_failures)
            _failsafe = Failsafe(retry_policy=policy, circuit_breaker=circuit_breaker)
            self.failsafe_list[url] = _failsafe

    async def run(self, fn, query_path, *args, **kwargs):
        for base_url, _failsafe in self.failsafe_list.items():
            url = urljoin(base_url, query_path)
            try:
                return await _failsafe.run(lambda: fn(url, *args, **kwargs))
            except FailsafeError:
                logging.debug("Executing fallback callable")


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

    def __init__(self, retry_policy=None, circuit_breaker=None):
        self.retry_policy = retry_policy or RetryPolicy(0)
        self.circuit_breaker = circuit_breaker or AlwaysClosedCircuitBreaker()

    async def run(self, callable):
        retry = True
        context = Context()

        while retry:
            if not self.circuit_breaker.allows_execution():
                logger.debug("Circuit open, stopping execution")
                raise CircuitOpen()

            try:
                context.attempts += 1
                result = await callable()
                self.circuit_breaker.record_success()
                return result

            except Exception as e:
                context.errors += 1
                retry = self.retry_policy.should_retry(context, e)
                self.circuit_breaker.record_failure()

                if retry:
                    logger.debug("Retrying call")

        raise RetriesExhausted()
