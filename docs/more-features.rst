More Features
-------------
.. currentmodule:: confugue

Overriding the callable
~~~~~~~~~~~~~~~~~~~~~~~
In addition to overriding the arguments of a callable (function or class), the configuaration file may also replace the callable itself using the :code:`class` key.
In a YAML file, the value needs to be specified using the :code:`!!python/name` tag (see the `PyYAML documentation <https://pyyaml.org/wiki/PyYAMLDocumentation#names-and-modules>`_ for more information):

.. code-block:: yaml

   ham:
     class: !!python/name:spam.Spam

Note that this is potentially unsafe, as it allows the configuration file to execute arbitrary code.
To load YAML files safely (which will disable this feature), pass :code:`loader=yaml.SafeLoader` to :meth:`from_yaml() <Configuration.from_yaml>` or :meth:`from_yaml_file() <Configuration.from_yaml_file>`.

Accessing raw values
~~~~~~~~~~~~~~~~~~~~
The raw content of a configuration object can be obtained by calling its :meth:`get() <Configuration.get>` method.
To access the value of a given key, use :code:`_cfg.get('key')` (equivalent to :code:`_cfg['key'].get()`).

Configuration lists
~~~~~~~~~~~~~~~~~~~
Sometimes we might want to create a list of objects of the same type, with arguments for each item supplied in the configuration file.
This can be useful for example when creating a deep neural network with layers of different sizes.
In this situation, we can use the :meth:`configure_list() <Configuration.configure_list>` method, like so::

   _cfg['fc_layers'].configure_list(tf.keras.layers.Dense, activation='relu')

The configuration file might then look like this:

.. code-block:: yaml

   fc_layers:
     - units: 100
     - units: 150
     - units: 2
       activation: None

Maybe configure
~~~~~~~~~~~~~~~
We have seen that we can omit parts of the configuration file as long as defaults for all the required parameters are defined in the code.
However, we might sometimes want to skip creating an object if the corresponding key is omitted from the configuration.
This functionality is provided by the :meth:`maybe_configure() <Configuration.maybe_configure>` method, which returns :code:`None` if the configuration value is missing.

Required parameters
~~~~~~~~~~~~~~~~~~~
Instead of providing a default value, it is possbile to explicitly mark a parameter as required::

   _cfg['dense_layer'].configure(tf.keras.layers.Dense, activation=_cfg.REQUIRED)

Not providing a value for this parameter in the configuration will result in an exception.
