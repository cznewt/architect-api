
=================
The Architect API
=================


In the Matrix the Architect was a highly specialized, humorless program of the
machine world as well as the creator of the Matrix. As the chief administrator
of the system, he is possibly a collective manifestation, or at the very least
a virtual representation of the entire Machine mainframe.

In our own reality the Architect is service modeling, management and
visualization platform. It's used by humans to create virtual representations
of software services and allow control thier entire life cycles.


Core Components
===============


Inventory
---------

Inventory is the Architect's metadata engine. It encapsulates and unifies data
from various metadata sources to provide inventory/metadata for various
orchestration services.


Manager
-------

Manager is the Architect's orchestration engine. It is very simple adapter
interface to various opensource orchestration engines.


Installation
============

Following steps show how to deploy various components of the Architect service
and connections to external services.


Service architect-api
---------------------

The core service responsible for handling HTTP API requests and providing
simple UI based on Material design.


Service architect-adapter
-------------------------

Managers that do not expose any form of API can be controlled locally by using
architect-adapter worker that wrap the local orchestration engine (Ansible,
Cloudify, TerraForm).


Salt Master inventory
---------------------

To enable Salt Master inventory, you need to install ``http_architect`` Pillar
and Top modules and add following to the Salt Master configuration files.

.. code-block:: yaml

    http_architect: &http_architect
      project: local-salt
      host: architect.service.host
      port: 8181

    ext_pillar:
      - http_architect: *http_architect

    master_tops:
      http_architect: *http_architect


Salt Master manager
-------------------

You can control salt master infrasturctue and get the status of managed hosts
and resources. The Salt engine ``architect`` relays the state outpusts of
individual state runs and ``architect`` runners and modules provide the
capabilities to interface with salt and architect functions. The Salt Master
is managed through it's HTTP API service.

.. code-block:: yaml

    http_architect: &http_architect
      project: newt.work
      host: 127.0.0.1
      port: 8181
