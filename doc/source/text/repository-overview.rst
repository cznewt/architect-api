
=======================
Image Building Overview
=======================

The architect is capable of pre-building images with specific content by
SaltStack. For this you need to setup the metadata model of the node and select
the Salt Master server. The procedure of building is:

#. Create the new inventory object (node definition), the ``reclass`` and
   ``cluster-deploy`` inventory types are supported.
#. Build the new image for the selected platform and node definition. The node
   does not need to be registered at Salt master, it can be added in process.