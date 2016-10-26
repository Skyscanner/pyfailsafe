# Change Log
All notable changes to this project will be documented in this file.

## [0.2.0]
### Added
- ExceptionHandlerPolicy: Replaces RetryPolicy extending its functionality with 
 abortable exceptions that will cause the failsafe run to finish.
### Removed
- RetryPolicy

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
- RetriesExhausted and FallbacksExhausted exceptions raise have the most recent exception attached as __cause__

## [0.0.1]
### Added
- Initial module created
