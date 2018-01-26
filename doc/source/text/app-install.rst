
============
Installation
============

Following steps show how to deploy various components of the Architect service
and connections to external services.


Service architect-api Installation
==================================

The core service responsible for handling HTTP API requests and providing
simple UI based on Material design. Release version of architect-api is
currently available on `Pypi <https://pypi.org/project/architect-api/>`_, to
install it, simply execute:

.. code-block:: bash

    pip install architect-api

To bootstrap latest development version into local virtualenv, run following
commands:

.. code-block:: bash

    git clone git@github.com:cznewt/architect-api.git
    cd architect-api
    virtualenv venv
    source venv/bin/activate
    python setup.py install

You provide one configuration file for all service settings. The default
location is ``/etc/architect/api.yaml``.


Service architect-client Installation
=====================================

Following steps show how to deploy and configure Architect Client.

.. code-block:: bash

    pip install architect-client

Create configuration file ``/etc/architect/client.yml`` for client.

.. code-block:: yaml

    project: project-name
    host: architect-api
    port: 8181
    username: salt
    password: password


SaltStack Integration
---------------------

To setup architect as Salt master Pillar source, set following configuration
to your Salt master at ``/etc/salt/master.d/_master.conf`` file.

.. code-block:: yaml

    ext_pillar:
      - cmd_yaml: 'architect-salt-pillar %s'

To setup architect as Salt master Tops source, set following configuration
to your Salt master at ``/etc/salt/master.d/_master.conf`` file.

.. code-block:: yaml

    master_tops:
       ext_nodes: architect-salt-top


You can test the SaltStack Pillar by calling command:

.. code-block:: bash

    $ architect-salt-pillar {{ minion-id }}


Ansible Integration
-------------------

To setup architect as Ansible dynamic inventory source, set following
configuration to your Ansible control node.

.. code-block:: bash

    $ ansible -i architect-ansible-inventory

You can test the ansible inventory by calling command:

.. code-block:: bash

    $ architect-ansible-inventory --list


Puppet Integration
------------------

To tell Puppet Server to use an ENC, you need to set two settings:
``node_terminus`` has to be set to “exec”, and ``external_nodes`` must have
the path to the executable.

.. code-block:: bash

    [master]
      node_terminus = exec
      external_nodes = /usr/local/bin/architect-puppet-classifier


Chef Integration
----------------

We can use ``-j`` parameter of ``chef-client`` command, It's the path to a
file that contains JSON data used to setup the client run. We pass

.. code-block:: bash

    $ architect-chef-data {{ node_name }} {{ file_name }}.json
    $ chef-client -j {{ file_name }}.json --environment _default
