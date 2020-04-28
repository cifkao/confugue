Confugue
========

Introduction
------------

`Confugue <https://github.com/cifkao/confugue>`_ is a hierarchical configuration framework for Python. It provides a wrapper class for nested configuration dictionaries (usually loaded from YAML files), which can be used to easily configure complicated object hierarchies.

The package is ideal for configuring deep learning experiments. These often have large numbers of hyperparameters, and managing all their values globally can quickly get tedious. Instead, Confugue allows each part of the deep learning model to be automatically supplied with hyperparameters from a configuration file, eliminating the need to pass them around. The structure of the configuration file follows the hierarchy of the model architecture; for example, if the model has multiple encoders consisting of several layers, then each layer will have its section in the configuration file, nested under the corresponding encoder section.

As an example, here is a simplified code snippet from a machine learning project which uses Confugue::

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


Contents
--------

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Contents

   Introduction <self>

.. toctree::
   :includehidden:
   :maxdepth: 2

   getting-started
   more-features
   api
   comparison
