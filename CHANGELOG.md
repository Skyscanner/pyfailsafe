# Change Log
All notable changes to this project will be documented in this file.

## [0.6.0]
### Added
- Added event handlers to `RetryPolicy` and `CircuitBreaker`.
- Added [unasync](https://unasync.readthedocs.io/en/latest/) library to the build, which creates sync versions of `Failsafe` and `FallbackFailsafe`

## [0.5.0]
### Changed
- Made the ``Failsafe.run()`` method accept all the ``*args`` and ``**kwargs`` from the original function.

## [0.4.0]
### Added
- Added half-open state, thus implementing Fowler's Circuit model (https://martinfowler.com/bliki/CircuitBreaker.html)

## [0.3.1]
### Changed
- `CircuitOpen` exceptions from tasks which trigger opening the circuit will now include the `__cause__`.

## [0.3.0]
### Added
- Add functionality to wait before executing a retry. There is a new `backoff` option in `RetryPolicy` which allows to define the wait time. (Thanks to @fcurella for this contribution!)

## [0.2.0]
### Added
- Extend `RetryPolicy`'s functionality with abortable exceptions that will cause `Failsafe` and `FallbackFailsafe` to abort execution immediately and raise the exception outside

## [0.1.3]
### Added
- Docstrings

## [0.1.1]
### Changed
- Pyfailsafe published to PyPI

## [0.1.0]
### Changed
- Project made public

## [0.0.2]
### Added
- `RetriesExhausted` and `FallbacksExhausted` exceptions raise have the most recent exception attached as __cause__

## [0.0.1]
### Added
- Initial module created
