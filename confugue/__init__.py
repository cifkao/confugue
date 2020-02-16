"""Confugue, a hierarchical configuration mechanism."""

import functools
import inspect
import logging
import sys

import wrapt
import yaml

from confugue.version import __version__

ALL = object()
REQUIRED = object()

_MISSING_VALUE = object()
_NO_DEFAULT = object()
_CFG_ATTR = '__confugue_cfg'
_PARAMS_ATTR = '__confugue_params'
_CFG_PARAM_ATTR = '__confugue_cfg_param'
_WRAPPED_ATTR = '__confugue_wrapped'

logger = logging.getLogger(__name__)


class Configuration:
    REQUIRED = REQUIRED

    def __init__(self, value=_MISSING_VALUE, name='<default>'):
        self._wrapped = value
        self.name = name
        self._child_configs = {}

    def get(self, key=None, default=_NO_DEFAULT):
        """Return an item from this configuration object.

        Returns:
            If `key` is given, the corresponding item from the wrapped object. Otherwise, the entire
            wrapped value. If the key is missing, `default` is returned instead (if given).
        Raises:
            KeyError: If the key is missing and no default was given.
            IndexError: If the key is missing and no default was given.
            TypeError: If the wrapped object does not support indexing.
        """
        if self._wrapped is _MISSING_VALUE:
            if default is _NO_DEFAULT:
                raise KeyError('Missing configuration value {}'.format(self._name_repr))
            return default

        if key is None:
            return self._wrapped

        if not hasattr(self._wrapped, '__getitem__'):
            raise TypeError('Attempted to get item {} of non-indexable configuration object {} '
                            'of type {}'.format(repr(key), self._name_repr, type(self._wrapped)))

        try:
            return self._wrapped[key]
        except (KeyError, IndexError) as e:
            if default is _NO_DEFAULT:
                raise type(e)("Missing configuration value '{}'".format(
                    self._get_key_name(key))) from None
            return default

    def configure(self, *args, **kwargs):
        """Configure an object using this configuration.

        One optional positional argument is expected: `constructor`.
        Calls `constructor` with the keyword arguments specified in this configuration object or
        passed to this function. Note that the constructor is called even if this configuration
        object corresponds to a missing key.

        Any keyword arguments passed to this function are treated as defaults and can be overridden
        by the configuration. A special `Configuration.REQUIRED` value can be used to mark a given
        key as required.

        Returns:
            The return value of `constructor`, or `None` if the value of this configuration object
            is `None`.
        """
        if len(args) > 1:
            raise TypeError('Expected at most 1 positional argument, got {}'.format(len(args)))
        constructor = args[0] if args else None

        config_val = self.get(default={})
        if config_val is None:
            return None

        return self._configure(self, config_val, constructor, kwargs)

    def maybe_configure(self, *args, **kwargs):
        """Configure an object only if a configuration is present.

        Like `configure`, but returns `None` if the configuration is missing.
        """
        if len(args) > 1:
            raise TypeError('Expected at most 1 positional argument, got {}'.format(len(args)))
        constructor = args[0] if args else None

        if self._wrapped is _MISSING_VALUE:
            return None

        return self.configure(constructor, **kwargs)

    def configure_list(self, *args, **kwargs):
        """Configure a list of objects.

        This method should be used if the configuration is expected to be a list. Every item of
        this list will then be used to configure a new object, as if `configure` was called on it.
        Any defaults supplied to this method will be used for all the items.
        """
        if len(args) > 1:
            raise TypeError('Expected at most 1 positional argument, got {}'.format(len(args)))
        constructor = args[0] if args else None

        config_val = self.get(default=[])
        if config_val is None:
            return None

        return [self._configure(self[i], config_item, constructor, kwargs)
                for i, config_item in enumerate(config_val)]

    def _configure(self, config, config_val, constructor, kwargs):
        # If config_value is not a dictionary, we just use the value as it is, unless the caller
        # has specified a constructor (in which case we raise an error).
        if type(config_val) is not dict:
            if constructor or kwargs:
                raise ConfigurationError('Error while configuring {}: dict expected, got {}'.format(
                    self._name_repr, type(config_val)))
            return config_val
        config_dict = dict(config_val)  # Make a copy of the dict

        try:
            # The 'class' key overrides the constructor passed by the caller (if any).
            if not constructor or 'class' in config_dict:
                try:
                    constructor = config_dict['class']
                except KeyError:
                    # If no constructor was specified anywhere, return the original dictionary.
                    return config_val

                del config_dict['class']
        except Exception as e:
            raise ConfigurationError('{} while configuring {}: {}'.format(
                type(e).__name__, self._name_repr, e
            )).with_traceback(sys.exc_info()[2]) from None

        # Check for missing required parameters.
        missing_keys = [repr(k) for k, v in kwargs.items()
                        if v is REQUIRED and k not in config_dict]
        if missing_keys:
            raise ConfigurationError('Error while configuring {}: required parameters {} missing '
                                     'from configuration'.format(
                                         self._name_repr, ', '.join(missing_keys)))

        # If the constructor is decorated with @configurable, we use _construct_configurable, which
        # creates a Configuration object and passes it to the constructor. Otherwise, we just call
        # the constructor.
        try:
            if hasattr(constructor, _WRAPPED_ATTR):
                return _construct_configurable(constructor, kwargs, config_dict, cfg=config)

            kwargs = {**kwargs, **config_dict}
            _log_call(constructor, kwargs=kwargs)
            return constructor(**kwargs)
        except TypeError as e:
            raise ConfigurationError('{} while configuring {} ({!r}): {}'.format(
                type(e).__name__, self._name_repr,
                getattr(constructor, _WRAPPED_ATTR, constructor), e
            )).with_traceback(sys.exc_info()[2]) from None

    def __getitem__(self, key):
        """Return a `Configuration` object corresponding to the given key.

        If the key is missing in the wrapped object, a `Configuration` object with a special
        `<missing>` value is returned.
        """
        if key not in self._child_configs:
            self._child_configs[key] = Configuration(self.get(key, _MISSING_VALUE),
                                                     name=self._get_key_name(key))
        return self._child_configs[key]

    def __setitem__(self, key, value):
        try:
            self._wrapped[key] = value
        except TypeError as e:
            raise TypeError('{}: {}'.format(self.name, e)) from None
        if key in self._child_configs:
            setattr(self._child_configs[key], '_wrapped', value)

    def __delitem__(self, key):
        try:
            del self._wrapped[key]
        except (KeyError, IndexError, TypeError) as e:
            raise type(e)('{}: {}'.format(self.name, e)) from None

    def __iter__(self):
        try:
            return iter(self._wrapped)
        except TypeError as e:
            raise TypeError('{}: {}'.format(self.name, e)) from None

    def __len__(self):
        try:
            return len(self._wrapped)
        except TypeError as e:
            raise TypeError('{}: {}'.format(self.name, e)) from None

    def __contains__(self, key):
        try:
            return self._wrapped is not _MISSING_VALUE and key in self._wrapped
        except TypeError as e:
            raise TypeError('{}: {}'.format(self.name, e)) from None

    def __bool__(self):
        return self._wrapped is not _MISSING_VALUE and bool(self._wrapped)

    def __repr__(self):
        return 'Configuration({}{})'.format(
            repr(self._wrapped) if self._wrapped is not _MISSING_VALUE else '<missing>',
            ', name={}'.format(self._name_repr) if not self._is_special_name else '')

    @property
    def _name_repr(self):
        return repr(self.name) if not self._is_special_name else self.name

    @property
    def _is_special_name(self):
        return self.name.startswith('<')

    def _get_key_name(self, key):
        if not self._is_special_name:
            return ('{}.{}' if isinstance(key, str) else '{}[{}]').format(self.name, key)
        return key if isinstance(key, str) else '[{}]'.format(key)

    @classmethod
    def from_yaml(cls, stream, loader=yaml.UnsafeLoader):
        return cls(yaml.load(stream, Loader=loader), '<root>')

    @classmethod
    def from_yaml_file(cls, stream, loader=yaml.UnsafeLoader):
        if isinstance(stream, str):
            with open(stream, 'rb') as f:
                return cls.from_yaml(f, loader)
        else:
            return cls.from_yaml(stream, loader)


# pylint: disable=missing-param-doc,missing-return-doc
def configurable(wrapped=None, *, params=ALL, cfg_property='_cfg', cfg_param='_cfg'):  # noqa: D417
    """A decorator that makes a function or a class configurable.

    The configurable function/class can be called/instantiated normally, or via
    `Configuration.configure`.

    If the decorated object is a function, it needs to define a keyword-only argument `_cfg`, which
    will be automatically filled with an instance of `Configuration` when the function is called.
    If the decorated object is a class, a `_cfg` property will be created containing the
    `Configuration` instance.

    Args:
        params: A list of configuration keys to pass as keyword arguments. The default behavior is
            to include all keys matching the function's signature, or all keys if the signature
            contains a `**` parameter.
        cfg_property: The name of the property that will hold the `Configuration` object in the
            case where a class is beging decorated (`_cfg` by default).
        cfg_param: The name of the parameter that will receive the `Configuration` object in
            the case where a function is being decorated (`_cfg` by default). This needs to be a
            keyword-only argument.
    """
    # The following is to allow the decorator to be used both with and without parentheses
    # (depending on whether or not the user wishes to pass arguments).
    if wrapped is None:
        return functools.partial(configurable, params=params, cfg_property=cfg_property)

    default_cfg = Configuration(_MISSING_VALUE)

    if inspect.isclass(wrapped):
        _add_cfg_property(wrapped, cfg_property, default_cfg)
        wrapper = wrapped
    else:
        argspec = inspect.getfullargspec(wrapped)

        # Check that the _cfg parameter is a keyword-only argument (if present)
        for arg_list in [argspec.args, argspec.varargs, argspec.varkw]:
            if arg_list and cfg_param in arg_list:
                raise ValueError("'{}' parameter defined in {}, but is not keyword-only"
                                 .format(cfg_param, wrapped))

        @wrapt.decorator(adapter=_update_configurable_argspec(argspec, cfg_param))
        def _configurable(wrapped, instance, args, kwargs):
            del instance
            if argspec.kwonlyargs and cfg_param in argspec.kwonlyargs:
                kwargs[cfg_param] = default_cfg
            return wrapped(*args, **kwargs)
        wrapper = _configurable(wrapped)  # pylint: disable=no-value-for-parameter
        setattr(wrapper, _CFG_PARAM_ATTR, cfg_param if cfg_param in argspec.kwonlyargs else None)

    setattr(wrapper, _WRAPPED_ATTR, wrapped)
    setattr(wrapper, _PARAMS_ATTR, params)

    return wrapper
# pylint: enable=missing-param-doc,missing-return-doc


def _add_cfg_property(cls, name, value):
    """Add the `_cfg` property to a class."""
    def _cfg_getter(self):
        if not hasattr(self, _CFG_ATTR):
            setattr(self, _CFG_ATTR, value)
        return getattr(self, _CFG_ATTR)

    setattr(cls, name, property(_cfg_getter))


def _update_configurable_argspec(argspec, cfg_param):
    """Return an updated `FullArgSpec` for a `@configurable` function."""
    return argspec._replace(
        kwonlyargs=argspec.kwonlyargs and [arg for arg in argspec.kwonlyargs if arg != cfg_param],
        kwonlydefaults=argspec.kwonlydefaults and {k: v for k, v in argspec.kwonlydefaults.items()
                                                   if k != cfg_param},
        annotations=argspec.annotations and {k: v for k, v in argspec.annotations.items()
                                             if k != cfg_param})


def _construct_configurable(x, kwargs, config_dict, cfg):
    # Determine which parameters to look for in the configuration
    param_names = getattr(x, _PARAMS_ATTR)
    if param_names is None:
        param_names = []
    elif param_names is ALL:
        params = inspect.signature(x).parameters.values()
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params):
            # If x accepts **kwargs, we take all values from the configuration
            param_names = config_dict.keys()
        else:
            # Otherwise take only keyword arguments defined in the signature
            param_names = [p.name for p in params
                           if p.kind not in [inspect.Parameter.VAR_POSITIONAL,
                                             inspect.Parameter.POSITIONAL_ONLY]]
    param_names = set(param_names)

    # Update kwargs with values from the config dict
    kwargs = dict(kwargs)
    kwargs.update({k: v for k, v in config_dict.items() if k in param_names})

    _log_call(x, kwargs=kwargs)

    if inspect.isclass(x):
        obj = x.__new__(x, **kwargs)
        setattr(obj, _CFG_ATTR, cfg)
        obj.__init__(**kwargs)
        return obj
    else:
        wrapped = getattr(x, _WRAPPED_ATTR)
        cfg_param = getattr(x, _CFG_PARAM_ATTR)
        if cfg_param is not None:
            kwargs[cfg_param] = cfg
        return wrapped(**kwargs)


def _log_call(fn, args=None, kwargs=None):
    args = args or []
    kwargs = kwargs or {}

    try:
        bound_args = inspect.signature(fn).bind(*args, **kwargs).arguments
        formatted_args = ['{}={!r}'.format(k, v) for k, v in bound_args.items()]
    except (TypeError, ValueError):
        formatted_args = ([repr(a) for a in args] +
                          ['{}={!r}'.format(k, v) for k, v in kwargs.items()])

    logger.debug('Calling {}({})'.format(fn.__name__, ', '.join(formatted_args)))


class ConfigurationError(Exception):
    pass
