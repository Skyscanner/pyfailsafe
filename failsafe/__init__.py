from .failsafe import Failsafe, FailsafeError, CircuitOpen, RetriesExhausted  # noqa
from .circuit_breaker import CircuitBreaker  # noqa
from .retry_policy import RetryPolicy, Delay, Backoff  # noqa
from .fallback_failsafe import FallbackFailsafe, FallbacksExhausted  # noqa

import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = '0.4.0'
