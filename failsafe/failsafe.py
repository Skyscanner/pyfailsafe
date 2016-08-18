from failsafe.circuit_breaker import AlwaysClosedCircuitBreaker
from failsafe.retry_policy import RetryPolicy


class Failsafe:

    def __init__(self, retry_policy=None, circuit_breaker=None):
        self.context = Context()
        self.retry_policy = retry_policy or RetryPolicy(0)
        self.circuit_breaker = circuit_breaker or AlwaysClosedCircuitBreaker()

    async def run(self, callable):
        callables = [(callable, self.circuit_breaker)]
        while callables:
            callable, circuit_breaker = callables.pop(0)
            retry = True
            self.context = Context()

            while retry:
                if circuit_breaker and not circuit_breaker.allows_execution():
                    if callables:
                        retry = False
                        continue
                    else:
                        raise CircuitOpen()

                try:
                    self.context.attempts += 1
                    result = await callable()
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    return result

                except Exception as e:
                    self.context.errors += 1
                    retry = self.retry_policy.should_retry(self.context, e) if self.retry_policy else False
                    if circuit_breaker:
                        circuit_breaker.record_failure()

        raise RetriesExhausted()


class CircuitOpen(Exception):
    pass


class Context(object):

    def __init__(self):
        self.attempts = 0
        self.errors = 0


class RetriesExhausted(Exception):
    pass
