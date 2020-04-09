Comparison to Other Frameworks
------------------------------

Gin
~~~

Confugue is somewhat similar to `Gin <https://github.com/google/gin-config>`_, but is much more minimalistic yet, in some ways, more powerful.
Some advantages of Confugue over Gin are:

- It is straightforward to configure many objects of the same type with different parameters for each; with Gin, this is possible, but it requires using scopes.
- Any function or class can be configured without having been explicitly registered. 
- Config files may override the type of an object (or the function being called) while preserving the default parameters provided by the caller.
- It is possible to access (and even manipulate) configuration values explicitly instead of (or in addition to) having them supplied as parameters.
- The structure of the config file is nested – typically following the call hierarchy – compared to Gin's linear structure.

On the other hand, Confugue doesn't have some of the advanced features of Gin, such as config file inclusion or 'operative configuration' logging. It also doesn't support macros, but a similar effect can be achieved using `PyYAML's aliases <https://pyyaml.org/wiki/PyYAMLDocumentation#aliases>`_.

Some other differences (which may be viewed as advantages or disadvantages in different situations) are:

- Gin config files specify *default* values for function parameters, which can be overridden by the caller. In Confugue, on the other hand, the config file has the final say.
- Gin will seamlessly load defaults from the configuration file every time a configurable function or class is called. Confugue is more explicit in that the caller first has to ask for a specific key from the configuration file.

Sacred
~~~~~~

`Sacred <https://github.com/IDSIA/sacred>`_ also offers configuration functionality, but its goals are much broader, focusing on experiment management (including keeping track of metrics and other information). Confugue, on the other hand, is not specifically targeted to scientific experimentation (even though it is particularly well suited for machine learning experiments). As for the configuration mechanism itself, Sacred has so-called 'captured functions' which resemble configurable functions in Confugue or Gin, but does not offer the same ability to configure arbitrary objects in a hierarchical way.

.. |build-status| image:: https://travis-ci.com/cifkao/confugue.svg?branch=master
   :target: https://travis-ci.com/cifkao/confugue
   :alt: Build Status
.. |docs-status| image:: https://readthedocs.org/projects/confugue/badge/?version=latest
   :target: https://confugue.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
