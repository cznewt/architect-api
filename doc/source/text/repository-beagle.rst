
=============================
BeagleBone/BeagleBoard Images
=============================

The BeagleBoard image builder used is fork of official Beagle image builder. To
install this image builder, clone repo
https://github.com/salt-formulas/beagleboard-image-builder to the location
specified in repository configuration.

.. literalinclude:: ../static/config/repository-beagle.yaml
   :language: yaml


Build Script
============

.. literalinclude:: ../../../utils/gen-image-bbb.sh
   :language: bash