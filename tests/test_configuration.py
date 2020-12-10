import pytest

from confugue import (Configuration, ConfigurationError, ConfigurationWarning,
                      configurable, logger)


def test_configure_function():
    @configurable
    def f(a, b, c, d, e=5, *, _cfg):
        return _cfg['obj'].configure(dict, a=a, b=b, c=c, d=d, e=e)

    result = Configuration({
        'a': 10, 'b': 2, 'c': 3,
        'obj': {'a': 1, 'f': 6}
    }).configure(f, a=0, c=300, d=4)
    expected_result = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6}
    assert result == expected_result


def test_configure_class():
    @configurable
    class A:

        def __init__(self, a, b, c, d, e=5):
            assert 'obj' in self._cfg
            self.obj = self._cfg['obj'].configure(dict, a=a, b=b, c=c, d=d, e=e)

    result = Configuration({
        'a': 10, 'b': 2, 'c': 3,
        'obj': {'a': 1, 'f': 6}
    }).configure(A, a=0, c=300, d=4).obj
    expected_result = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6}
    assert result == expected_result


def test_bind():
    @configurable
    class A:

        def __init__(self, a, b, c, d, e=5):
            assert 'obj' in self._cfg
            self.obj = self._cfg['obj'].bind(dict, a=a, c=c, d=d, e=e)(b=b)

    result = Configuration({
        'a': 10, 'b': 2, 'c': 3,
        'obj': {'a': 1, 'f': 6}
    }).bind(A, a=0, c=300)(d=4).obj
    expected_result = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6}
    assert result == expected_result


def test_configure_list():
    @configurable
    def f(*, _cfg):
        return _cfg['items'].configure_list(f)

    result = Configuration({
        'items': [
            {'class': dict, 'x': 1},
            {'items': [{'class': dict, 'y': 2}, {'class': dict, 'z': 3}]}
        ]
    }).configure(f)
    expected_result = [{'x': 1}, [{'y': 2}, {'z': 3}]]
    assert result == expected_result


def test_maybe_configure():
    @configurable
    def f(*, _cfg):
        return (_cfg['missing'].maybe_configure(dict),
                _cfg['present'].maybe_configure(dict))

    result = Configuration({
        'present': {'a': 1}
    }).configure(f)
    expected_result = (None, {'a': 1})
    assert result == expected_result


def test_none_value():
    @configurable
    def f(*, _cfg):
        return _cfg.get('a')

    result = Configuration(None).configure(f, a=1)
    assert result is None


def test_configurable_with_params():
    @configurable(params=['a', 'c'])
    def f(a, b, c, d=4, *, _cfg):
        del _cfg
        return a, b, c, d

    result = Configuration({'a': 1, 'b': None, 'c': 3, 'd': 4}).configure(f, b=2)
    expected_result = (1, 2, 3, 4)
    assert result == expected_result


def test_configurable_with_kwargs():
    @configurable
    def f(a, *, _cfg, **kwargs):
        del _cfg
        return a, kwargs

    result = Configuration({'a': 1, 'c': 3}).configure(f, b=2)
    expected_result = (1, {'b': 2, 'c': 3})
    assert result == expected_result


def test_invalid_cfg_parameter():
    with pytest.raises(ValueError) as excinfo:
        @configurable
        def f(a=1, _cfg=None):
            del a, _cfg
        del f
    logger.debug(excinfo.exconly())


def test_required():
    cfg = Configuration({'present': 1})
    with pytest.raises(ConfigurationError) as excinfo:
        cfg.configure(dict, missing=cfg.REQUIRED)
    logger.debug(excinfo.exconly())
    assert "'missing'" in str(excinfo.value)
    assert "'present'" not in str(excinfo.value)


def test_get_unused_keys():
    @configurable
    def f(a, b, *, _cfg):
        _cfg['g'].configure()
        _cfg['g_list'].configure_list(g)

    @configurable
    def g(a):
        pass

    cfg = Configuration({
        'a': 1, 'b': 2,
        'unused': {'a': 1, 'b': 2},
        'g': {'class': g, 'a': 1, 'unused': 2},
        'g_list': [{'a': 1, 'unused': 2}],
        'x': {'a': 1, 'unused': {'b': 2}},
    })
    cfg.configure(f)
    cfg['x']['a'].get()
    cfg['unused']  # we are not accessing the value

    with pytest.warns(ConfigurationWarning):
        unused_keys = cfg.get_unused_keys(warn=True)
    assert set(unused_keys) == {'unused', 'g.unused', 'g_list[0].unused', 'x.unused'}


def test_get_unused_keys_with_all_children_used():
    cfg = Configuration({
        'a': {'x': 1, 'y': 2}
    })
    cfg['a']['x'].get()
    cfg['a']['y'].get()

    assert cfg.get_unused_keys() == []
