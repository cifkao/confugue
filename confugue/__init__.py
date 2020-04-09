"""Confugue, a hierarchical configuration mechanism."""

import functools
import inspect
import logging
import sys
import warnings

import wrapt
import yaml

from confugue.version import __version__


class _SpecialValue:

    def __init__(self, rep):
        self._rep = rep

    def __repr__(self):
        return self._rep


ALL = _SpecialValue('ALL')
REQUIRED = _SpecialValue('REQUIRED')

_MISSING_VALUE = _SpecialValue('MISSING_VALUE')
_NO_DEFAULT = _SpecialValue('NO_DEFAULT')
_CFG_ATTR = '__confugue_cfg'
_PARAMS_ATTR = '__confugue_params'
_CFG_PARAM_ATTR = '__confugue_cfg_param'
_WRAPPED_ATTR = '__confugue_wrapped'

logger = logging.getLogger(__name__)


class Configuration:
    """Wrapper for nested configuration dictionaries or lists.

    The core functionality is provided by the :meth:`configure` method, which calls a given
    callable with the arguments from the wrapped dictionary.

    If the wrapped value is a dictionary or a list, basic operations such as indexing and iteration
    are supported, with the values recursively wrapped in :class:`Configuration` objects. If the
    user tries to access a key or index which is missing, an "empty" configuration object is
    returned; this can still be used normally and behaves more or less as if it contained an empty
    dictionary.

    The wrapped value may be of any other type, but in this case, most of the methods will raise
    an exception. To retrieve the raw wrapped value (whatever the type), use the :meth:`get` method
    with no arguments.
    """

    REQUIRED = REQUIRED

    def __init__(self, value=_MISSING_VALUE, name='<root>'):
        self._wrapped = value
        self.name = name
        self.parent = None
        self._parent_key = None
        self._child_configs = {}
        self._used_keys = set()

    def get(self, key=None, default=_NO_DEFAULT):
        """Return an item from this configuration object (assuming the wrapped value is indexable).

        Returns:
            If `key` is given, the corresponding item from the wrapped object. Otherwise, the entire
            wrapped value. If the value is missing, `default` is returned instead (if given).
        Raises:
            KeyError: If the value is missing and no default was given.
            IndexError: If the value is missing and no default was given.
            TypeError: If the wrapped object does not support indexing.
        """
        return self._get(key, default, mark_used=True)

    def _get(self, key, default, mark_used=False):
        if self._wrapped is _MISSING_VALUE:
            if default is _NO_DEFAULT:
                raise KeyError('Missing configuration value {}'.format(self._name_repr))
            return default

        if key is None:
            if mark_used:
                self._mark_used()
            return self._wrapped

        if not hasattr(self._wrapped, '__getitem__'):
            raise TypeError('Attempted to get item {} of non-indexable configuration object {} '
                            'of type {}'.format(repr(key), self._name_repr, type(self._wrapped)))

        try:
            value = self._wrapped[key]
            if mark_used:
                self._used_keys.add(key)
            return value
        except (KeyError, IndexError) as e:
            if default is _NO_DEFAULT:
                raise type(e)("Missing configuration value '{}'".format(
                    self._get_key_name(key))) from None
            return default

    def configure(self, *args, **kwargs):
        """Configure a callable using this configuration.

        Calls `constructor` with the keyword arguments specified in this configuration object or
        passed to this method. Note that the constructor is called even if this configuration
        object corresponds to a missing key. `constructor` may be overridden in by a `class`
        configuration key (if the `constructor` parameter is not given, then the `class` key is
        required).

        Any keyword arguments passed to this method are treated as defaults and can be overridden
        by the configuration. A special :attr:`Configuration.REQUIRED` value can be used to mark a
        given key as required.

        Returns:
            The return value of `constructor`, or `None` if the wrapped value is `None`.
        Raises:
            ConfigurationError: If the wrapped value is not a dict, if required arguments are
                missing, or if any exception occurs while calling `constructor`.
        """
        return self._configure(args, kwargs)

    def bind(self, *args, **kwargs):
        """Configure a callable without calling it.

        Like :meth:`configure`, but instead of calling `constructor` directly, it returns a new
        function that calls `constructor` with parameters bound to the supplied values. The
        function may still accept other parameters.

        Returns:
            A function, or `None` if the wrapped value is `None`.
        Raises:
            ConfigurationError: If the wrapped value is not a dict, or if required arguments are
                missing.
        """
        return self._configure(args, kwargs, bind_only=True)

    def maybe_configure(self, *args, **kwargs):
        """Configure a callable only if the configuration is present.

        Like :meth:`configure`, but returns `None` if the configuration is missing.

        Returns:
            The return value of `constructor`, or `None` if the wrapped value is missing or `None`.
        Raises:
            ConfigurationError: If the wrapped value is not a dict, if required arguments are
                missing, or if any exception occurs while calling `constructor`.
        """
        return self._configure(args, kwargs, maybe=True)

    def maybe_bind(self, *args, **kwargs):
        """Configure a callable without calling it, but only if the configuration is present.

        Like :meth:`bind`, but returns `None` if the configuration is missing.

        Returns:
            A function, or `None` if the wrapped value is missing or `None`.
        Raises:
            ConfigurationError: If the wrapped value is not a dict, or if required arguments are
                missing.
        """
        return self._configure(args, kwargs, maybe=True, bind_only=True)

    def _configure(self, args, kwargs, maybe=False, bind_only=False):
        if len(args) > 1:
            raise TypeError('Expected at most 1 positional argument, got {}'.format(len(args)))
        constructor = args[0] if args else None

        if maybe and self._wrapped is _MISSING_VALUE:
            self._mark_used()
            return None

        config_val = self._get(key=None, default={}, mark_used=True)
        if config_val is None:
            return None

        return self._configure_impl(config_val, constructor, kwargs, bind_only)

    def configure_list(self, *args, **kwargs):
        """Configure a list of objects.

        This method should be used if the configuration is expected to be a list. Every item of
        this list will then be used to configure a new object, as if :meth:`configure` was called on
        it. Any defaults supplied to this method will be used for all the items.

        Returns:
            A list containing the values obtained by configuring `constructor`, in turn, using all
            the dicts in the wrapped list; `None` if the wrapped value is `None`.
        Raises:
            ConfigurationError: If the wrapped value is not a list of dicts, if required arguments
                are missing, or if any exception occurs while calling `constructor`.
        """
        if len(args) > 1:
            raise TypeError('Expected at most 1 positional argument, got {}'.format(len(args)))
        constructor = args[0] if args else None

        config_val = self._get(key=None, default=[], mark_used=True)
        if config_val is None:
            return None

        return [self[i]._configure_impl(config_item, constructor, kwargs)  # pylint: disable=protected-access
                for i, config_item in enumerate(config_val)]

    def _configure_impl(self, config_val, constructor, kwargs, bind_only=False):
        # If config_value is not a dictionary, we just use the value as it is, unless the caller
        # has specified a constructor (in which case we raise an error).
        if type(config_val) is not dict:
            if constructor or kwargs or bind_only:
                raise ConfigurationError('Error while configuring {}: dict expected, got {}'.format(
                    self._name_repr, type(config_val)))
            return config_val
        config_dict = dict(config_val)  # Make a copy of the dict

        # The 'class' key overrides the constructor passed by the caller (if any).
        if not constructor or 'class' in config_dict:
            try:
                constructor = config_dict['class']
                del config_dict['class']
            except KeyError:
                raise ConfigurationError('Error while configuring {}: No constructor (class) '
                                         'specified'.format(self._name_repr)) from None

        # Check for missing required parameters.
        missing_keys = [repr(k) for k, v in kwargs.items()
                        if v is REQUIRED and k not in config_dict]
        if missing_keys:
            raise ConfigurationError('Error while configuring {}: required parameter(s) {} missing '
                                     'from configuration'.format(
                                         self._name_repr, ', '.join(missing_keys)))

        # If the constructor is decorated with @configurable, we use _construct_configurable, which
        # creates a Configuration object and passes it to the constructor. Otherwise, we just call
        # the constructor.
        try:
            if hasattr(constructor, _WRAPPED_ATTR):
                result, used_keys = _construct_configurable(constructor, kwargs, config_dict,
                                                            cfg=self, bind_only=bind_only)
                self._used_keys.update(used_keys)
            else:
                kwargs = {**kwargs, **config_dict}
                _log_call(constructor, kwargs=kwargs, bind_only=bind_only)
                if bind_only:
                    result = functools.partial(constructor, **kwargs)
                else:
                    result = constructor(**kwargs)
                self._used_keys.update(config_dict.keys())
            return result
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError('{} while configuring {} ({!r})'.format(
                type(e).__name__, self._name_repr,
                getattr(constructor, _WRAPPED_ATTR, constructor)
            )) from e

    def __getitem__(self, key):
        """Return a :class:`Configuration` object corresponding to the given key.

        If the key is missing in the wrapped object, a :class:`Configuration` object with a special
        `<missing>` value is returned.
        """
        if key not in self._child_configs:
            cfg = Configuration(self._get(key, _MISSING_VALUE),
                                name=self._get_key_name(key))
            cfg.parent = self
            cfg._parent_key = key
            self._child_configs[key] = cfg
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
        if key in self._child_configs:
            del self._child_configs[key]

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

    def get_unused_keys(self, warn=False):
        """Recursively find keys that were never accessed.

        Args:
            warn: If `True`, a warning will be issued if unused keys are found.
        Returns:
            A list of unused keys.
        """
        if type(self._wrapped) is dict:
            keys = self._wrapped.keys()
        elif type(self._wrapped) is list:
            keys = range(len(self._wrapped))
        else:
            keys = []

        unused_keys = []
        for key in keys:
            child_unused_keys = []
            # Report the unused keys in this subtree iff there are also some used keys.
            if (key in self._child_configs and
                    self._child_configs[key]._has_used_keys()):  # pylint: disable=protected-access
                child_unused_keys = self._child_configs[key].get_unused_keys()
            unused_keys.extend(child_unused_keys)
            # Only report this key if no key from its subtree was reported above.
            if not child_unused_keys and key not in self._used_keys:
                unused_keys.append(self._get_key_name(key))

        if unused_keys and warn:
            warnings.warn('Found {} unused keys: {}'.format(len(unused_keys),
                                                            ', '.join(unused_keys)),
                          ConfigurationWarning)

        return unused_keys

    def _has_used_keys(self):
        return (len(self._used_keys) > 0 or
                any(cfg._has_used_keys()  # pylint: disable=protected-access
                    for cfg in self._child_configs.values()))

    def _mark_used(self):
        if self.parent is not None and self._parent_key is not None:
            self.parent._used_keys.add(self._parent_key)  # pylint: disable=protected-access

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
        """Create a configuration from YAML.

        The configuration is loaded using PyYAML's :class:`UnsafeLoader` by default. If you wish
        to load configuration files from untrusted sources, you should pass
        :code:`loader=yaml.SafeLoader`.

        Args:
            stream: A YAML string or an open file object.
            loader: One of PyYAML's loader classes.
        Returns:
            A :class:`Configuration` instance wrapping the loaded configuration.
        """
        return cls(yaml.load(stream, Loader=loader))

    @classmethod
    def from_yaml_file(cls, stream, loader=yaml.UnsafeLoader):
        """Create a configuration from a YAML file.

        The configuration is loaded using PyYAML's :class:`UnsafeLoader` by default. If you wish
        to load configuration files from untrusted sources, you should pass
        :code:`loader=yaml.SafeLoader`.

        Args:
            stream: A path to a YAML file, or an open file object.
            loader: One of PyYAML's loader classes.
        Returns:
            A :class:`Configuration` instance wrapping the loaded configuration.
        """
        if isinstance(stream, str):
            with open(stream, 'rb') as f:
                return cls.from_yaml(f, loader)
        else:
            return cls.from_yaml(stream, loader)


# pylint: disable=missing-param-doc,missing-return-doc
def configurable(wrapped=None, *, params=ALL, cfg_property='_cfg', cfg_param='_cfg'):  # noqa: D417
    """A decorator that makes a function or a class configurable.

    The decorator may be used with or without parentheses (i.e. both :code:`@configurable`
    and :code:`@configurable()` is valid).

    If the decorated callable is a function or method, it needs to define a keyword-only argument
    :code:`_cfg`, which will be automatically filled with an instance of :class:`Configuration`
    when the function is called. If the decorated callable is a class, a :code:`_cfg` property will
    be created holding the :class:`Configuration` instance.

    The decorated function/class can be called/instantiated normally (without passing the `_cfg`
    argument), or via :meth:`Configuration.configure`.

    Args:
        params: A list of configuration keys to pass as keyword arguments. The default behavior is
            to include all keys matching the function's signature, or all keys if the signature
            contains a `**` parameter.
        cfg_property: The name of the property that will hold the :class:`Configuration` object in
            the case where a class is beging decorated.
        cfg_param: The name of the parameter that will receive the :class:`Configuration` object in
            the case where a function is being decorated. This needs to be a keyword-only
            parameter.
    """
    # The following is to allow the decorator to be used both with and without parentheses
    # (depending on whether or not the user wishes to pass arguments).
    if wrapped is None:
        return functools.partial(
            configurable, params=params, cfg_property=cfg_property, cfg_param=cfg_param)

    default_cfg = Configuration(_MISSING_VALUE, name='<default>')

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
    """Return an updated :class:`FullArgSpec` for a configurable function."""
    return argspec._replace(
        kwonlyargs=argspec.kwonlyargs and [arg for arg in argspec.kwonlyargs if arg != cfg_param],
        kwonlydefaults=argspec.kwonlydefaults and {k: v for k, v in argspec.kwonlydefaults.items()
                                                   if k != cfg_param},
        annotations=argspec.annotations and {k: v for k, v in argspec.annotations.items()
                                             if k != cfg_param})


def _construct_configurable(x, kwargs, config_dict, cfg, bind_only):
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

    # Create a wrapper so that we can use functools.partial on it if bind_only is True
    @functools.wraps(x)
    def wrapper(**kwargs):
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

    _log_call(x, kwargs=kwargs, bind_only=bind_only)

    if bind_only:
        return functools.partial(wrapper, **kwargs), param_names
    else:
        return wrapper(**kwargs), param_names


def _log_call(fn, args=None, kwargs=None, bind_only=False):
    args = args or []
    kwargs = kwargs or {}

    try:
        bound_args = inspect.signature(fn).bind(*args, **kwargs).arguments
        formatted_args = ['{}={!r}'.format(k, v) for k, v in bound_args.items()]
    except (TypeError, ValueError):
        formatted_args = ([repr(a) for a in args] +
                          ['{}={!r}'.format(k, v) for k, v in kwargs.items()])

    logger.debug('{} {}({})'.format('Binding' if bind_only else 'Calling',
                                    fn.__name__, ', '.join(formatted_args)))


class ConfigurationError(Exception):
    pass


class ConfigurationWarning(Warning):
    pass
