class RetryPolicy:

    def __init__(self, allowed_retries=3, retriable_exception=None):
        self.allowed_retries = allowed_retries
        self.retriable_exception = retriable_exception

    def should_retry(self, context, exception=None):
        return context.attempts <= self.allowed_retries and self._is_expected_exception(exception)

    def _is_expected_exception(self, exception):
        return isinstance(exception, self.retriable_exception) if self.retriable_exception else True
