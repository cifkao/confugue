Getting Started -- General Guide
--------------------------------
.. currentmodule:: confugue

.. Tip:: Deep learning users should check out the :doc:`deep-learning` with examples in PyTorch.


First, we need a function or class to configure. Let's start with a simple function like this::

   def main(foo, bar, baz):
       print(foo, bar, baz)

Next, we need to create a :class:`Configuration` object. Typically, we will do this by loading a YAML config file::

   from confugue import Configuration

   config = Configuration.from_yaml_file('config.yaml')

:code:`config` now acts as a wrapper for the contents of :file:`config.yaml`, and can be used to configure our :code:`main()` function, like so::

   config.configure(main, foo=1, bar=2)  # baz needs to be set in config.yaml

The code above will call :code:`main()` with the given arguments, plus any arguments defined in the configuration. The values specified in the code are treated as defaults and can be overridden by the configuration. For example, if :file:`config.yaml` looks like this...

.. code-block:: yaml

   foo: ham
   baz: spam

...then the above code will call :code:`main(foo='ham', bar=2, baz='spam')`.

Hierarchical configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

Although any function or class can be configured as described above, in order to make full use of Confugue, we need to decorate our functions and classes with the :func:`@configurable <configurable>` decorator.
This enables them to access values from their parent :class:`Configuration` object, and use them to further configure other functions or class instances.
Decorated functions and classes each behave a bit differently:

- A :func:`@configurable <configurable>` class automatically obtains a magic :code:`_cfg` property containing the parent configuration object. The property is set immediately upon the creation of the object, so that it can already be used in :code:`__init__`.
- A :func:`@configurable <configurable>` function (or method) should define a `keyword-only parameter <https://python-3-for-scientists.readthedocs.io/en/latest/python3_advanced.html#keyword-only-arguments>`_ :code:`_cfg` (see below for an example of how to do that), which will receive the parent configuration object.

For example::

   from confugue import configurable

   @configurable
   def main(foo, bar=456, *, _cfg):
       print('main', foo, bar)
       ham1 = _cfg['ham1'].configure(Ham)
       ham2 = _cfg['ham2'].configure(Ham)

   @configurable
   class Ham:

       def __init__(self, x):
           print('Ham', x)
           self._egg = self._cfg['egg'].configure(Egg, y=0)

   class Egg:

       def __init__(self, y):
           print('Egg', y)

   config = Configuration.from_yaml_file('config2.yaml')
   config.configure(main)

Now, given the following :file:`config2.yaml`...

.. code-block:: yaml

   foo: 123
   ham1:
     x: 1
     egg:
       y: 2
   ham2:
     x: 3

...we will get this output:

.. code-block:: none

   main 123 456
   Ham 1
   Egg 2
   Ham 3
   Egg 0


.. admonition:: How does it work?

  When we call :code:`config.configure(main)`, the following happens:

  - The :code:`foo` value defined in the config file gets passed as an argument to :code:`main()`. The values :code:`ham1` and :code:`ham2`, however, do not get passed as arguments since the function does not accept them, and instead become available via :code:`_cfg`.
  - :code:`_cfg['ham1']` retrieves the :code:`ham1` config dictionary and wraps it in a new :class:`Configuration` object, ready to configure a new instance of :code:`Ham`.
  - Similarly, inside :code:`Ham`'s constructor, the value under :code:`ham1 -> egg` is retrieved and used to configure an :code:`Egg` instance.

  Notice how :code:`self._cfg['egg'].configure(Egg, y=0)` works even though there is no :code:`ham2 -> egg` key in the config file.
  This is because :code:`self._cfg['egg']` returns an empty :class:`Configuration` object, which will happily instantiate :code:`Egg` as long as a default value for :code:`y` is provided in the code.

.. admonition:: Keep in mind
  :class: tip

  - When calling a configurable, Confugue looks at its function signature and matches the configuration keys against it. Only the matching keys are passed as arguments (unless the signature contains a :code:`**kwargs` argument, in which case all keys will be used).
    This behavior can be changed by passing a list of configurable parameters as the :code:`params` argument of the :func:`@configurable <configurable>` decorator.
  - A configurable can still be called normally (rather than using :meth:`configure <Configuration.configure>`). :code:`_cfg` will be automatically set to a default configuration object, which will behave as if the configuration file was empty.
  - The :func:`@configurable <configurable>` decorator is necessary only if the function or class needs to access its configuration (:code:`_cfg`).
  - Instead of loading a YAML file, one can use any other configuration dictionary by directly calling :code:`Configuration(cfg_dict)`.

.. seealso:: Advanced features are described in :doc:`more-features`.
