class RetryPolicy:

    def __init__(self, retries=0, exception=None):
        self.retries = retries
        self.exception = exception

    def should_retry(self, context, exception=None):
        is_expected_exception = isinstance(exception, self.exception) if self.exception else True
        return context.attempts <= self.retries and is_expected_exception
