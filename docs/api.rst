API Reference
-------------
.. currentmodule:: confugue

.. autodecorator:: configurable(\*, params=ALL, cfg_property='_cfg', cfg_param='_cfg')

.. autoclass:: Configuration
   :members: from_yaml, from_yaml_file

   .. automethod:: configure(constructor=None, /, \*\*kwargs)

   .. automethod:: maybe_configure(constructor=None, /, \*\*kwargs)

   .. automethod:: configure_list(constructor=None, /, \*\*kwargs)

   .. automethod:: bind(constructor=None, /, \*\*kwargs)

   .. automethod:: maybe_bind(constructor=None, /, \*\*kwargs)

   .. automethod:: get

   .. automethod:: get_unused_keys

.. autoclass:: ConfigurationError
