from failsafe.failsafe import Context
from failsafe.retry_policy import RetryPolicy


class TestRetryPolicy:

    def test_should_retry_when_attempts_is_less_then_limit(self):
        retry_policy = RetryPolicy(allowed_retries=3)

        context = Context()
        context.attempts = 3

        assert retry_policy.should_retry(context) is True

    def test_should_not_retry_when_there_were_too_many_attempts(self):
        retry_policy = RetryPolicy(allowed_retries=3)

        context = Context()
        context.attempts = 4

        assert retry_policy.should_retry(context) is False

    def test_should_not_retry_when_exception_is_not_retriable(self):
        retry_policy = RetryPolicy(allowed_retries=3, retriable_exceptions=[BufferError])

        context = Context()
        context.attempts = 3

        assert retry_policy.should_retry(context, ArithmeticError()) is False

    def test_should_retry_when_exception_is_retriable(self):
        retry_policy = RetryPolicy(allowed_retries=3, retriable_exceptions=[BufferError])

        context = Context()
        context.attempts = 3

        assert retry_policy.should_retry(context, BufferError()) is True

    def test_should_not_retry_when_exception_is_retriable_but_there_were_too_many_attempts(self):
        retry_policy = RetryPolicy(allowed_retries=3, retriable_exceptions=[BufferError])

        context = Context()
        context.attempts = 4

        assert retry_policy.should_retry(context, BufferError()) is False

    def test_should_retry_with_more_that_one_exception_type(self):
        retry_policy = RetryPolicy(allowed_retries=3, retriable_exceptions=[BufferError, ValueError])

        context = Context()
        context.attempts = 3

        assert retry_policy.should_retry(context, BufferError()) is True
        assert retry_policy.should_retry(context, ValueError()) is True
