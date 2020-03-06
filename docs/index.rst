.. confugue documentation master file, created by
   sphinx-quickstart on Mon Feb 17 13:20:05 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. currentmodule:: confugue

confugue
========

:mod:`confugue` is a hierarchical configuration framework for Python. It provides a wrapper class for nested configuration dictionaries (usually loaded from YAML files), which can be used to configure complicated object hierarchies in a recursive fashion.

As an example, here is a simplified code snippet from a machine learning project which uses :mod:`confugue`::

   @configurable
   class Model:

       def __init__(self, vocabulary, use_sampling=False):
           self.embeddings = self._cfg['embedding_layer'].configure(EmbeddingLayer,
                                                                    input_size=len(vocabulary))
           self.decoder = self._cfg['decoder'].configure(RNNDecoder,
                                                         vocabulary=vocabulary,
                                                         embedding_layer=self.embeddings)

   @configurable
   class RNNDecoder:

       def __init__(self, vocabulary, embedding_layer):
           self.cell = self._cfg['cell'].configure(tf.keras.layers.GRUCell,
                                                   units=100,
                                                   dtype=tf.float32)
           self.output_projection = self._cfg['output_projection'].configure(
               tf.layers.Dense,
               units=len(vocabulary),
               use_bias=False)

The model could then be configured using the following config file, overriding the values specified in the code and filling in the ones that are missing.

.. code-block:: yaml

   embedding_layer:
     output_size: 300
   decoder:
     cell:
       class: !!python/name:tensorflow.keras.layers.LSTMCell
       units: 1024
   use_sampling: True

Getting started
---------------

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

Although any function or class can be configured in this way, in order to make use of the hierarchical mechanism, we need to decorate our functions and classes with the :func:`configurable` decorator. This enables them to access values from their parent :class:`Configuration` object, and use them to further configure other functions or class instances, as shown in the introductory example.
Decorated functions and classes each behave a bit differently:

- A :code:`@configurable` function (or method) must define a keyword-only parameter :code:`_cfg`, which will be used to pass the parent configuration object.
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

Additional features
-------------------

Maybe configure
~~~~~~~~~~~~~~~
We have seen that we can omit parts of the configuration file as long as defaults for all the required parameters are defined in the code.
However, we might sometimes want to skip creating an object if the corresponding key is omitted from the configuration.
This functionality is provided by the :meth:`Configurable.maybe_configure` method, which returns :code:`None` if the configuration value is missing.

Configuring lists
~~~~~~~~~~~~~~~~~
We might also want to create a list of objects of the same type, with arguments supplied in the configuration file.
This can be useful for example when creating a deep neural network with layers of different sizes.
In this situation, we can use the :meth:`Configurable.configure_list` method, like so::

   _cfg['fc_layers'].configure_list(tf.keras.layers.Dense, activation='relu')

The configuration file might then look like this:

.. code-block:: yaml

   fc_layers:
     - units: 100
     - units: 150
     - units: 2
       activation: None

Required parameters
~~~~~~~~~~~~~~~~~~~
Instead of providing a default value, it is possbile to explicitly mark a parameter as required::

   _cfg['dense_layer'].configure(tf.keras.layers.Dense, activation=_cfg.REQUIRED)

Not providing a value for this parameter in the configuration will result in an exception.

API Reference
-------------

.. autoclass:: Configuration
   :members: get

   .. automethod:: configure(constructor=None, /, \*\*kwargs)

   .. automethod:: maybe_configure(constructor=None, /, \*\*kwargs)

   .. automethod:: configure_list(constructor=None, /, \*\*kwargs)


.. autodecorator:: configurable(\*, params=ALL, cfg_property='_cfg', cfg_param='_cfg')

