from failsafe.circuit_breaker import AlwaysClosedCircuitBreaker
from failsafe.retry_policy import RetryPolicy


class Failsafe:

    def __init__(self, retry_policy=None, circuit_breaker=None):
        self.retry_policy = retry_policy or RetryPolicy(0)
        self.circuit_breaker = circuit_breaker or AlwaysClosedCircuitBreaker()

    async def run(self, callable):
        retry = True
        context = Context()

        while retry:
            if not self.circuit_breaker.allows_execution():
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

        raise RetriesExhausted()


class CircuitOpen(Exception):
    pass


class Context(object):

    def __init__(self):
        self.attempts = 0
        self.errors = 0


class RetriesExhausted(Exception):
    pass
