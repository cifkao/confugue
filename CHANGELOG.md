# Changelog

## [0.1.1]

### Fixed
- 'class' key being incorrectly reported as unused ([#3](https://github.com/cifkao/confugue/issues/3)).

## [0.1.0]

### Added
- `get_unused_keys` method.
- `bind` and `maybe_bind` methods.

### Fixed
- Handle all exceptions raised while calling the callable (by mistake, only some were being handled) and use proper exception chaining.


[0.1.0]: https://github.com/cifkao/confugue/compare/v0.0.1...v0.1.0
[0.1.1]: https://github.com/cifkao/confugue/compare/v0.1.0...v0.1.1
[unreleased]: https://github.com/cifkao/confugue/compare/v0.1.1...HEAD
