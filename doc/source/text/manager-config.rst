
========================
Configuration Management
========================


SaltStack Infrastructures
=========================

Configuration for connecting to Salt API endpoint.

.. literalinclude:: ../static/config/manager-saltstack.yaml
   :language: yaml

Following figure shows how SaltStack integrates with Architect Inventory and
Manager. Please note that you can use Inventory integration independently of
the Manager integration.

.. figure:: ../static/scheme/manager_salt.png
    :align: center
    :width: 70%

The metadata schema for SaltStack manager:

.. literalinclude:: ../../../architect/schemas/saltstack.yaml
   :language: yaml


Salt Master Integration
-----------------------

You can control salt master infrastructure and get the status of managed hosts
and resources. The Salt engine ``architect`` relays the state outputs of
individual state runs and ``architect`` runners and modules provide the
capabilities to interface with salt and architect functions. The Salt Master
is managed through it's HTTP API service.

.. code-block:: yaml

    http_architect: &http_architect
      project: newt.work
      host: 127.0.0.1
      port: 8181
