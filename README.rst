Confugue
========

|build-status| |docs-status|

:code:`confugue` is a hierarchical configuration framework for Python. It provides a wrapper class for nested configuration dictionaries (usually loaded from YAML files), which can be used to configure complicated object hierarchies in a recursive fashion.

As an example, here is a simplified code snippet from a machine learning project which uses :code:`confugue`:

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

.. |build-status| image:: https://travis-ci.com/cifkao/confugue.svg?branch=master
   :target: https://travis-ci.com/cifkao/confugue
   :alt: Build Status
.. |docs-status| image:: https://readthedocs.org/projects/confugue/badge/?version=latest
   :target: https://confugue.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
