Getting Started
---------------
.. currentmodule:: confugue


First, we need to create a :class:`Configuration` object::

   from confugue import Configuration

   config = Configuration.from_yaml_file('config.yaml')

:code:`config` now acts as a wrapper for the contents of :file:`config.yaml`, and can be used to configure a function or class constructor, like so::

   config.configure(main, foo=1, bar=2)

The code above will call :code:`main` with the given arguments, plus any arguments defined in the configuration. The values specified in the code are treated as defaults and can be overridden by the configuration. For example, if :file:`config.yaml` looks like this...

.. code-block:: yaml

   foo: ham
   baz: spam

...then the above code will call :code:`main(foo='ham', bar=2, baz='spam')`.

Hierarchical configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

Although any function or class can be configured as described above, in order to make use of the hierarchical configuration mechanism, we need to decorate our functions and classes with the :func:`configurable` decorator.
This enables them to access values from their parent :class:`Configuration` object, and use them to further configure other functions or class instances.
Decorated functions and classes each behave a bit differently:

- A :code:`@configurable` function (or method) should define a `keyword-only parameter <https://python-3-for-scientists.readthedocs.io/en/latest/python3_advanced.html#keyword-only-arguments>`_ :code:`_cfg` (see below for an example of how to do that), which will be used to pass the parent configuration object.
- A :code:`@configurable` class automatically receives a magic :code:`_cfg` property containing the parent configuration object. The property is set immediately upon the creation of the object, so that it can already be used in :code:`__init__`.

In both cases, it is still possible to call the decorated function or class normally (rather than via :meth:`Configuration.configure`) with the same result as if the configuration file was empty.

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

...we will get the following output:

.. code-block:: none

   main 123 456
   Ham 1
   Egg 2
   Ham 3
   Egg 0

What happens when we call :code:`config.configure(main)` is the following:

- The values :code:`ham1` and :code:`ham2` defined in the config file do not get passed as arguments to :code:`main` since they are not present in its signature; instead, they become available via :code:`_cfg`.
- :code:`_cfg['ham1']` retrieves the :code:`ham1` config dictionary and wraps it in a new :class:`Configuration` object, ready to configure a new instance of :code:`Ham`.
- Similarly, inside :code:`Ham`'s constructor, the value under :code:`ham1 -> egg` is retrieved and used to configure an :code:`Egg` instance.

Notice how :code:`self._cfg['egg'].configure(Egg, y=0)` still works in the second case, even though there is no :code:`ham2 -> egg` key in the config file.
This is because :code:`self._cfg['egg']` returns an empty :class:`Configuration` object, which will happily instantiate :code:`Egg` as long as a default value for :code:`y` is provided in the code.

