More Features
-------------

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
