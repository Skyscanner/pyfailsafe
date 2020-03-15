# Pyfailsafe
[![Build Status](https://travis-ci.org/Skyscanner/pyfailsafe.svg)](https://travis-ci.org/Skyscanner/pyfailsafe)
[![PyPI](https://img.shields.io/pypi/v/pyfailsafe.svg)](https://pypi.python.org/pypi/pyfailsafe)

A Python library for handling failures, heavily inspired by the Java project [Failsafe](https://github.com/jhalterman/failsafe).

Pyfailsafe provides mechanisms for dealing with operations that inherently can fail, such as calls to external services. It takes advantage of the Python's coroutines and only supports async operations and Python 3.5.

* [Basic usage](#bare-failsafe-call)
* [Retries](#failsafe-call-with-retries)
* [Circuit breakers](#circuit-breakers)
* [Chained calls - fallbacks](#making-http-calls-with-fallbacks)
* [Using Pyfailsafe to make HTTP calls](#using-pyfailsafe-to-make-http-calls)
* [Examples](#examples)

## Installation

To get started using Pyfailsafe, install with

```sh
pip install pyfailsafe
```

then read the rest of this document to learn how to use it.

## Usage

### Bare Failsafe call

```python
from failsafe import Failsafe

async def my_async_function():
    return 'done'

# this is the same as just calling:
# result = await my_async_function()
result = await Failsafe().run(my_async_function)
assert result == 'done'
```

### Failsafe call with retries

Use `RetryPolicy` class to define the number of retries which should be made before operation fails.

```python
from failsafe import Failsafe, RetryPolicy

async def my_async_function():
    raise Exception()  # by default, every exception will cause a retry

retry_policy = RetryPolicy(allowed_retries=3)

await Failsafe(retry_policy=retry_policy).run(my_async_function)
# raises failsafe.RetriesExhausted
# my_async_function was called 4 times (1 regular call + 3 retries)
```

By default, retries are executed immediately - there is no backoff.
If you want to wait before executing a retry, you can use the `backoff` parameter:

```python
from datetime import timedelta
from failsafe import Failsafe, RetryPolicy, Delay

async def my_async_function():
    raise Exception()  # by default, every exception will cause a retry

delay = Delay(timedelta(seconds=5))
retry_policy = RetryPolicy(allowed_retries=3, backoff=delay)

await Failsafe(retry_policy=retry_policy).run(my_async_function)
# raises failsafe.RetriesExhausted
# my_async_function was called 4 times, waiting for 5 seconds between each call.
```

We also ship a `Backoff` class that supports jitter and incremental delay

```python
from datetime import timedelta
from failsafe import Failsafe, RetryPolicy, Backoff

async def my_async_function():
    raise Exception()  # by default, every exception will cause a retry

backoff = Backoff(
    delay=timedelta(seconds=2),  # the initial delay
    max_delay=timedelta(seconds=15),
    jitter=False  # if True, the wait time will be random between 0 and the actual time for this attempt
)
retry_policy = RetryPolicy(allowed_retries=3, backoff=backoff)

await Failsafe(retry_policy=retry_policy).run(my_async_function)
# raises failsafe.RetriesExhausted
# my_async_function was called 4 times, waiting for 2, 4 and 8 seconds respectively.
```

It is possible to provide your own backoff logic by subclassing the
`failsafe.retry_logic.Backoff` class and overriding the `.for_attempt(attempt)` method.

It is possible to specify a particular set of exceptions that should cause a retry - any exception not contained in that set will cause immediate failure instead.

```python
from failsafe import Failsafe, RetryPolicy

async def my_async_function():
    return 3/0

retry_policy = RetryPolicy(allowed_retries=3, retriable_exceptions=[ZeroDivisionError])

await Failsafe(retry_policy=retry_policy).run(my_async_function)
# raises failsafe.RetriesExhausted
# my_async_function was called 4 times (1 regular call + 3 retries)
```

```python
from failsafe import Failsafe, RetryPolicy

async def my_async_function():
    raise TypeError()

retry_policy = RetryPolicy(allowed_retries=3, retriable_exceptions=[ZeroDivisionError])

await Failsafe(retry_policy=retry_policy).run(my_async_function)
# TypeError is not ZeroDivisionError, so my_async_function was called just once in this example
```

RetryPolicy instances are immutable and thread-safe. They can be safely shared between Failsafe instances.

### Failsafe call with abortable exceptions

If you need your code to be able to raise certain exceptions that should not be handled by the failsafe,
you can add them as abortable_exceptions in RetryPolicy. This is useful when you know that the nature of failure was
such that consecutive calls would never succeed.

```python
from failsafe import Failsafe, RetryPolicy

async def my_async_function():
    raise ValueError()  # ValueError is an abortable exception, so it will not cause retry

retry_policy = RetryPolicy(allowed_retries=4, abortable_exceptions=[ValueError])

await Failsafe(retry_policy=retry_policy).run(my_async_function)
# raises ValueError
# my_async_function was called 1 time (1 regular call)
```

### Circuit breakers

[Circuit breakers](http://martinfowler.com/bliki/CircuitBreaker.html) are a way of creating systems that fail-fast by temporarily disabling execution as a way of preventing system overload.

```python
from failsafe import Failsafe, CircuitBreaker

async def my_async_function():
    raise Exception()

circuit_breaker = CircuitBreaker(maximum_failures=3, reset_timeout_seconds=60)
failsafe = Failsafe(circuit_breaker=circuit_breaker)

await failsafe.run(my_async_function)
await failsafe.run(my_async_function)
await failsafe.run(my_async_function)
# now circuit breaker will get open and other calls to Failsafe.run will
# immediately raise the failsafe.CircuitOpen exception and the passed
# function will not even be called.
# Circuit will be closed again in 60 seconds.
```

A circuit breaker instance can and should be shared across code that accesses inter-dependent system components that fail together. This ensures that if the circuit is opened, executions against one component that rely on another component will not be allowed until the circuit is closed again.

A circuit breaker instance is stateful - it remembers how many failures occur and whether the circuit is open or closed.

A circuit breaker will not take into account abortable exceptions.

#### CircuitBreaker interface

A CircuitBreaker can also be manually operated in a standalone way:

```python
from failsafe import CircuitBreaker

circuit_breaker = CircuitBreaker()

circuit_breaker.open()  # executions won't be allowed when circuit breaker is open
circuit_breaker.close()
circuit_breaker.current_state  # 'open' or 'closed'

if circuit_breaker.allows_execution():
    try:
        do_something()
        circuit_breaker.report_success()
    except:
        circuit_breaker.report_failure()
```

#### Circuit breaker with retries

It is recommended to use circuit breakers together with retry policies. Every failed retry will count as a failure to the circuit breaker.

```python
from failsafe import Failsafe, CircuitBreaker, RetryPolicy

async def my_async_function():
    raise Exception()

circuit_breaker = CircuitBreaker()
retry_policy = RetryPolicy()
failsafe = Failsafe(circuit_breaker=circuit_breaker, retry_policy=retry_policy)
await failsafe.run(my_async_function)
```

### Using Pyfailsafe to make HTTP calls

Failsafe is not dependent on any HTTP client library, so a function making a call has to be provided by the developer. Said function must return a coroutine.

The example below uses aiohttp client to make a call.

```python
from failsafe import Failsafe, RetryPolicy, CircuitBreaker, FailsafeError
import aiohttp

circuit_breaker = CircuitBreaker()
retry_policy = RetryPolicy()
failsafe = Failsafe(circuit_breaker=circuit_breaker, retry_policy=retry_policy)

async def make_get_request(url):
    async def _make_get_request(_url):
        with aiohttp.ClientSession() as session:
            async with session.get(_url) as resp:
                if resp.status != 200:
                    raise Exception()  # exception tells Failsafe to retry
                return await resp.json()

    try:
        return await failsafe.run(_make_get_request, url)
    except FailsafeError:
        raise RuntimeError("Error while getting data")


if __name__ == "__main__":
    async def print_response():
        from pprint import pprint
        result = await make_get_request('https://api.github.com/users/skyscanner/repos')
        pprint(result)


    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(print_response())
    loop.close()
```

#### Making HTTP calls with fallbacks

Use FallbackFailsafe class to simplify handling fallbacks:

```python
import aiohttp
from urllib.parse import urljoin

from failsafe import FallbackFailsafe

class SortingClient:
    def __init__(self):
        endpoint_main = "http://eu-west-1.sorting-service.local"
        endpoint_secondary = "http://eu-central-1.sorting-service.local"

        self.fallback_failsafe = FallbackFailsafe([endpoint_main, endpoint_secondary])

    async def get_sorting(self, name, age):
        query_path = "/v1/sort/name/{0}/age/{1}".format(name, age)
        return await self.fallback_failsafe.run(self._request, query_path)

    async def _request(self, endpoint, query_path):
        url = urljoin(endpoint, query_path)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise Exception()
                return await resp.json()
```

## Examples

It is recommended to wrap calls in the class which will abstract away the outside service.

Check [examples](examples) folder for comprehensive examples of how Pyfailsafe should be used. See [examples/README.md](examples/README.md) to run examples.

## Developing

When making changes to the module it is always a good idea to run everything within a python virtual environment to ensure isolation of dependencies.

```sh
# Python 3.5 or greater needed
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_test.txt
```

Unit tests are written using pytest and can be run from the root of the project with

```sh
py.test tests/ -v
```

Coding standards are maintained using the flake8 tool which will run as part of the build process. To run locally simply use:

```sh
flake8 failsafe/ tests/ examples/
```

## Publishing

1. Set new version number in `failsafe/init.py` and commit it
2. `git tag X.Y.Z`
3. `git push --tags`

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) file to add a contribution.

Maintainers:

- https://github.com/jakubka
- https://github.com/carl0FF
- https://github.com/cajturner
