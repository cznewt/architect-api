
=============================
Architect Inventory Consumers
=============================


SaltStack Consumer
==================


``http_architect`` pillar backend
---------------------------------

To enable Salt Master inventory, you need to install ``http_architect`` Pillar
and Top modules and add following to the Salt Master configuration files. To
support the grains.

.. code-block:: yaml

    http_architect: &http_architect
      project: local-salt
      host: architect.service.host
      port: 8181

    ext_pillar:
      - http_architect: *http_architect

    master_tops:
      http_architect: *http_architect


Native pillar backend
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


References
----------

* https://docs.saltstack.com/en/latest/ref/tops/all/salt.tops.ext_nodes.html
* https://docs.saltstack.com/en/latest/ref/pillar/all/salt.pillar.cmd_yaml.html#module-salt.pillar.cmd_yaml


Ansible Consumer
================

To setup architect as Ansible dynamic inventory source, set following
configuration to your Ansible control node.

.. code-block:: bash

    $ ansible -i architect-ansible-inventory

You can test the ansible inventory by calling command:

.. code-block:: bash

    $ architect-ansible-inventory --list


References
----------

* http://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html


Puppet Consumer
===============

To tell Puppet Server to use an ENC, you need to set two settings:
``node_terminus`` has to be set to “exec”, and ``external_nodes`` must have
the path to the executable.

.. code-block:: bash

    [master]
      node_terminus = exec
      external_nodes = /usr/local/bin/architect-puppet-classifier


References
----------

* https://puppet.com/docs/puppet/5.3/nodes_external.html


Chef Consumer
=============

We can use ``-j`` parameter of ``chef-client`` command, It's the path to a
file that contains JSON data used to setup the client run. We pass

.. code-block:: bash

    $ architect-chef-data {{ node_name }} {{ file_name }}.json
    $ chef-client -j {{ file_name }}.json --environment _default


References
----------

* https://docs.chef.io/ctl_chef_client.html
