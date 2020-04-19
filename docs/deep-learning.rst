Deep Learning Quick Start Guide
-------------------------------
.. currentmodule:: confugue

This section is intended as a quick start guide for deep learning users.
It is based on PyTorch examples, but it should be easy to follow even for people working with other frameworks like TensorFlow.

.. admonition:: Not into deep learning?

   Confugue is absolutely not limited to machine learning applications.
   Python users unfamiliar with deep learning should check out the :doc:`General Guide <general-guide>`.

.. Tip:: This guide is available as a `Jupyter notebook <https://github.com/cifkao/confugue/blob/master/docs/pytorch_tutorial.ipynb>`_.
   |colab-link|

   .. |colab-link| image:: https://colab.research.google.com/assets/colab-badge.svg
      :target: https://colab.research.google.com/github/cifkao/confugue/blob/master/docs/pytorch_tutorial.ipynb
      :alt: Open in Colab

Basic PyTorch example
~~~~~~~~~~~~~~~~~~~~~
We are going to start with a basic PyTorch model, adapted from the `CIFAR-10 tutorial <https://pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html>`_.
First, let's see what the model looks like *without* using Confugue::

   from torch import nn

   class Net(nn.Module):

       def __init__(self):
           super(Net, self).__init__()
           self.conv1 = nn.Conv2d(3, 6, 5)
           self.conv2 = nn.Conv2d(6, 16, 5)
           self.pool = nn.MaxPool2d(2, 2)
           self.fc1 = nn.Linear(400, 120)
           self.fc2 = nn.Linear(120, 10)
           self.act = nn.ReLU()

       def forward(self, x):
           x = self.pool(self.act(self.conv1(x)))
           x = self.pool(self.act(self.conv2(x)))
           x = x.flatten(start_dim=1)
           x = self.act(self.fc1(x))
           x = self.fc2(x)
           return x

Making it configurable
~~~~~~~~~~~~~~~~~~~~~~
Instead of hard-coding all the hyperparameters like above, we want to be able to specify them in a configuration file. To do so, we are going to decorate our class with the :func:`@configurable <configurable>` decorator. This provides it with a magic :code:`_cfg` property, giving it access to the configuration. We can then rewrite our :code:`__init__` as follows::

   from confugue import configurable, Configuration

   @configurable
   class Net(nn.Module):

       def __init__(self):
           super(Net, self).__init__()
           self.conv1 = self._cfg['conv1'].configure(nn.Conv2d, in_channels=3)
           self.conv2 = self._cfg['conv2'].configure(nn.Conv2d)
           self.pool = self._cfg['pool'].configure(nn.MaxPool2d)
           self.fc1 = self._cfg['fc1'].configure(nn.Linear)
           self.fc2 = self._cfg['fc2'].configure(nn.Linear, out_features=10)
           self.act = self._cfg['act'].configure(nn.ReLU)

       def forward(self, x):
           x = self.pool(self.act(self.conv1(x)))
           x = self.pool(self.act(self.conv2(x)))
           x = x.flatten(start_dim=1)
           x = self.act(self.fc1(x))
           x = self.fc2(x)
           return x

Instead of creating each layer directly, we configure it with values from the corresponding section of the configuration file (which we will see in a moment).
Notice that we can still specify arguments in the code (e.g. :code:`in_channels=3` for the :code:`conv1` layer), but these are treated as defaults and can be overridden in the configuration file if needed.

Loading configuration from a YAML file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Calling :code:`Net()` directly would result in an error, since we haven't specified defaults for all the required parameters of each layer.
We therefore need to create a configuration file :file:`config.yaml` to supply them:

.. code-block:: yaml

   conv1:
     out_channels: 6
     kernel_size: 5
   conv2:
     in_channels: 6
     out_channels: 16
     kernel_size: 5
   pool:
     kernel_size: 2
     stride: 2
   fc1:
     in_features: 400
     out_features: 120
   fc2:
     in_features: 120

.. Note:: We do not need to include the activation function (:code:`act`), since it does not have any
   required parameters. We could, however, :ref:`override the type <Overriding the callable>`
   of the activation function itself.

We are now ready to load the file into a Configuration object and use it to configure our network::

   >>> cfg = Configuration.from_yaml_file('config.yaml')
   >>> cfg
   Configuration({'conv1': {'out_channels': 6, 'kernel_size': 5}, 'conv2': {'in_channels': 6, 'out_channels': 16, 'kernel_size': 5}, 'pool': {'kernel_size': 2, 'stride': 2}, 'fc1': {'in_features': 400, 'out_features': 120}, 'fc2': {'in_features': 120}})
   >>> cfg.configure(Net)
   Net(
     (conv1): Conv2d(3, 6, kernel_size=(5, 5), stride=(1, 1))
     (conv2): Conv2d(6, 16, kernel_size=(5, 5), stride=(1, 1))
     (pool): MaxPool2d(kernel_size=2, stride=2, padding=0, dilation=1, ceil_mode=False)
     (fc1): Linear(in_features=400, out_features=120, bias=True)
     (fc2): Linear(in_features=120, out_features=10, bias=True)
     (act): ReLU()
   )

.. Tip:: Instead of loading a YAML file, one can use any configuration dictionary by directly calling :code:`Configurable(cfg_dict)`.

Nested configurables
~~~~~~~~~~~~~~~~~~~~
One of the most useful features of Confugue is that :func:`@configurable <configurable>` classes and functions can use other configurables, and the structure of the configuration file will naturally follow this hierarchy.
To see this in action, we are going to write a configurable :code:`main` function which trains our simple model on the CIFAR-10 dataset.

.. code-block::

   import torchvision
   from torchvision import transforms

   @configurable
   def main(num_epochs=1, log_period=2000, *, _cfg):
       net = _cfg['net'].configure(Net)
       criterion = _cfg['loss'].configure(nn.CrossEntropyLoss)
       optimizer = _cfg['optimizer'].configure(torch.optim.SGD, params=net.parameters(),
					       lr=0.001)

       transform = transforms.Compose(
           [transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
       train_data = torchvision.datasets.CIFAR10(root='./data', train=True,
						 download=True, transform=transform)
       train_loader = _cfg['data_loader'].configure(torch.utils.data.DataLoader,
						    dataset=train_data, batch_size=4,
						    shuffle=True, num_workers=2)

       for epoch in range(num_epochs):
           for i, batch in enumerate(train_loader):
               inputs, labels = batch
               optimizer.zero_grad()
               loss = criterion(net(inputs), labels)
               loss.backward()
               optimizer.step()

               if (i + 1) % log_period == 0:
                   print(i + 1, loss.item())

Our :file:`config.yaml` might then look like this:

.. code-block:: yaml

   net:
     conv1:
       out_channels: 6
       kernel_size: 5
     conv2:
       in_channels: 6
       out_channels: 16
       kernel_size: 5
     pool:
       kernel_size: 2
       stride: 2
     fc1:
       in_features: 400
       out_features: 120
     fc2:
       in_features: 120

   optimizer:
     class: !!python/name:torch.optim.Adam
   data_loader:
     batch_size: 8
   num_epochs: 2
   log_period: 1000

To create and train our model::

   cfg = Configuration.from_yaml_file('config.yaml')
   cfg.configure(main)

Configuring lists
~~~~~~~~~~~~~~~~~

The :meth:`configure_list <Configuration.configure_list>` method allows us to configure a list of objects, with the parameters for each supplied from the
configuration file. We are going to use this, in conjunction with :code:`nn.Sequential`, to fully specify the model in the configuration file, so we won't
need our :code:`Net` class anymore.

.. code-block:: yaml

   layers:
     - class: !!python/name:torch.nn.Conv2d
       in_channels: 3
       out_channels: 6
       kernel_size: 5
     - class: !!python/name:torch.nn.ReLU
     - class: !!python/name:torch.nn.MaxPool2d
       kernel_size: 2
       stride: 2
     - class: !!python/name:torch.nn.Conv2d
       in_channels: 6
       out_channels: 16
       kernel_size: 5
     - class: !!python/name:torch.nn.ReLU
     - class: !!python/name:torch.nn.MaxPool2d
       kernel_size: 2
       stride: 2
     - class: !!python/name:torch.nn.Flatten
     - class: !!python/name:torch.nn.Linear
       in_features: 400
       out_features: 120
     - class: !!python/name:torch.nn.ReLU
     - class: !!python/name:torch.nn.Linear
       in_features: 120
       out_features: 10

Creating the model then becomes a matter of two lines of code::

   >>> cfg = Configuration.from_yaml_file('config.yaml')
   >>> nn.Sequential(*cfg['layers'].configure_list())
   Sequential(
     (0): Conv2d(3, 6, kernel_size=(5, 5), stride=(1, 1))
     (1): ReLU()
     (2): MaxPool2d(kernel_size=2, stride=2, padding=0, dilation=1, ceil_mode=False)
     (3): Conv2d(6, 16, kernel_size=(5, 5), stride=(1, 1))
     (4): ReLU()
     (5): MaxPool2d(kernel_size=2, stride=2, padding=0, dilation=1, ceil_mode=False)
     (6): Flatten()
     (7): Linear(in_features=400, out_features=120, bias=True)
     (8): ReLU()
     (9): Linear(in_features=120, out_features=10, bias=True)
   )

This offers a lot of flexibility, but it should be used with care. If your configuration file is longer than your code, you might be overusing it.


.. seealso:: Advanced features are described in :doc:`more-features`.
