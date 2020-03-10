Confugue
========

|build-status| |docs-status|

Confugue is a hierarchical configuration framework for Python. It provides a wrapper class for nested configuration dictionaries (usually loaded from YAML files), which can be used to easily configure complicated object hierarchies.

The package is ideal for configuring deep learning experiments. These often have large numbers of hyperparameters, and managing all their values globally can quickly get tedious. Instead, Confugue allows each part of the deep learning model to be automatically supplied with hyperparameters from a YAML configuration file, eliminating the need to pass them around. The nested structure of the configuration file follows the hierarchy of the model architecture, with each part of the model having access to the corresponding section of the file.

As an example, here is a simplified code snippet from a deep learning project which uses Confugue:

.. code-block:: python

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

Installation & Documentation
----------------------------

A full documentation can be found `here <https://confugue.readthedocs.io/>`_.

The package is available from PyPI and can be installed with :code:`pip install confugue`.

Comparison with other frameworks
--------------------------------

Gin
~~~

Confugue is similar to `Gin <https://github.com/google/gin-config>`_, but is much more minimalistic yet still very powerful.
Some advantages of Confugue over Gin are:

- It is straightforward to configure many objects of the same type with different parameters for each; with Gin, this is possible, but it requires using a scoping mechanism.
- Any function or class can be configured without having been explicitly registered. 
- Config files may override the type of an object (or the function being called) while preserving the default parameters provided by the caller.
- It is possible to access (and even manipulate) configuration values explicitly instead of (or in addition to) having them supplied as parameters.
- The structure of the config file is nested – typically following the call hierarchy – compared to Gin's linear structure.

On the other hand, Confugue doesn't have some of the advanced features of Gin, such as config file inclusion or 'operative configuration' logging. It also doesn't support macros, but `PyYAML's aliases <https://pyyaml.org/wiki/PyYAMLDocumentation#aliases>`_ provide similar functionality.

Some other differences (which may be viewed as advantages or disadvantages in different situations) are:

- Gin config files specify *default* values for function parameters, which can be overridden by the caller. In Confugue, on the other hand, the config file has the final say.
- Gin will seamlessly load defaults from the configuration file every time a configurable function or class is called. Confugue is more explicit in that the caller first has to ask for a specific key from the configuration file.

Sacred
~~~~~~

`Sacred <https://github.com/IDSIA/sacred>`_ also offers configuration functionality, but its goals are much broader, focusing on experiment managament (including keeping track of metrics and other information). Confugue, on the other hand, is not specifically targeted to scientific experimentation (even though it is particularly well suited for machine learning experiments). As for the configuration mechanism itself, Sacred has so-called 'captured functions' which work similarly to configurable functions in Confugue or Gin, but does not offer the same ability to configure arbitrary objects in a hierarchical way.

.. |build-status| image:: https://travis-ci.com/cifkao/confugue.svg?branch=master
   :target: https://travis-ci.com/cifkao/confugue
   :alt: Build Status
.. |docs-status| image:: https://readthedocs.org/projects/confugue/badge/?version=latest
   :target: https://confugue.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
