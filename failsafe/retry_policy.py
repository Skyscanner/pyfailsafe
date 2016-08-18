class RetryPolicy:

    def __init__(self, allowed_retries=3, retriable_exceptions=None):
        self.allowed_retries = allowed_retries
        self.retriable_exceptions = retriable_exceptions or []

    def should_retry(self, context, exception=None):
        return context.attempts <= self.allowed_retries and self._is_expected_exception(exception)

    def _is_expected_exception(self, exception):
        return any(isinstance(exception, e) for e in self.retriable_exceptions) if self.retriable_exceptions else True
