# Changelog

## [Unreleased]

### Added
- `get_unused_keys` method.
- `bind` and `maybe_bind` methods.

### Fixed
- Handle all exceptions raised while calling the callable (by mistake, only some were being handled) and use proper exception chaining.

[unreleased]: https://github.com/cifkao/confugue/compare/v0.0.1...HEAD
