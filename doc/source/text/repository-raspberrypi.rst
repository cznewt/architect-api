
==================
RaspberryPi Images
==================

The Raspberry Pi image builder used is fork of official Beagle image builder. To
install this image builder, clone repo
https://github.com/salt-formulas/rpi23-gen-image to the location
specified in repository configuration.

.. literalinclude:: ../static/config/repository-raspberry.yaml
   :language: yaml


Build Script
============

The ``rpi23-gen-image`` uses modified generator script.

.. literalinclude:: ../../../utils/gen-image-rpi23.sh
   :language: bash