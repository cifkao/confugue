API Reference
-------------
.. currentmodule:: confugue

.. autodecorator:: configurable(\*, params=ALL, cfg_property='_cfg', cfg_param='_cfg')

.. autoclass:: Configuration

   .. automethod:: configure(constructor: Optional[Callable] = None, /, \*\*kwargs) -> Any

   .. automethod:: maybe_configure(constructor: Optional[Callable] = None, /, \*\*kwargs) -> Any

   .. automethod:: configure_list(constructor: Optional[Callable] = None, /, \*\*kwargs) -> Optional[List]

   .. automethod:: bind(constructor: Optional[Callable] = None, /, \*\*kwargs) -> Optional[Callable]

   .. automethod:: maybe_bind(constructor: Optional[Callable] = None, /, \*\*kwargs) -> Optional[Callable]

   .. automethod:: get

   .. automethod:: get_unused_keys

   .. automethod:: from_yaml(stream: str | bytes | TextIO | BinaryIO, loader=yaml.Loader) -> Configuration

   .. automethod:: from_yaml_file(stream: str | TextIO | BinaryIO, loader=yaml.Loader) -> Configuration

.. autoclass:: interactive

.. autoclass:: ConfigurationError

.. autoclass:: ConfigurationWarning
