import datetime


class RetryPolicy:

    def __init__(self, retries=0, exception=None):
        self.retries = retries
        self.exception = exception

    def should_retry(self, context, exception=None):
        is_expected_exception = isinstance(exception, self.exception) if self.exception else True
        return context.attempts <= self.retries and is_expected_exception


class FailSafe:

    def __init__(self, retry_policy=None):
        self.context = Context()
        self.retry_policy = retry_policy or RetryPolicy(0)
        self.fallback_callable = None
        self.fallback_circuit_breaker = None

    def with_fallback(self, fallback_callable, circuit_breaker=None):
        self.fallback_callable = fallback_callable
        self.fallback_circuit_breaker = circuit_breaker
        return self

    async def run(self, callable, circuit_breaker=None):
        callables = [(callable, circuit_breaker)]
        if self.fallback_callable is not None:
            callables.append((self.fallback_callable, self.fallback_circuit_breaker))

        while callables:
            callable, circuit_breaker = callables.pop(0)
            retry = True
            self.context = Context()

            while retry:
                if circuit_breaker and not circuit_breaker.allows_requests():
                    if callables:
                        retry = False
                        continue
                    else:
                        raise CircuitOpen()

                try:
                    self.context.attempts += 1
                    coroutine = callable()
                    result = await coroutine
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    return result

                except Exception as e:
                    self.context.errors += 1
                    retry = self.retry_policy.should_retry(self.context, e) if self.retry_policy else False
                    if circuit_breaker:
                        circuit_breaker.record_failure()

        raise NoMoreFallbacks()


class CircuitOpen(Exception):
    pass


class CircuitBreaker:

    def __init__(self, threshold=0):
        self.successes = []
        self.failures = []
        self.threshold = threshold

    def allows_requests(self):
        if not self.failures:
            return True

        failures_in_last_second = [x for x in self.failures
                                   if x >= datetime.datetime.now() - datetime.timedelta(seconds=10)]
        return len(failures_in_last_second) <= self.threshold

    def record_success(self):
        self.successes.append(datetime.datetime.now())

    def record_failure(self):
        self.failures.append(datetime.datetime.now())


class Context(object):

    def __init__(self):
        self.attempts = 0
        self.errors = 0


class NoMoreFallbacks(Exception):
    pass
