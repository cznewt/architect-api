
============================
Template Based Orchestration
============================


Heat Templates
==============


Heat templates with local context (env) definitions.

.. literalinclude:: ../static/config/manager-heat-local.yaml
   :language: yaml

Heat templates with remote context (env) definitions coming from Inventory
service.

.. literalinclude:: ../static/config/manager-heat-remote.yaml
   :language: yaml

The metadata schema for Heat manager:

.. literalinclude:: ../../../architect/schemas/heat.yaml
   :language: yaml


References
----------

* https://docs.openstack.org/heat/pike/template_guide/openstack.html
* https://github.com/openstack/heat-templates


TerraForm Templates
===================

Configuration for parsing Hashicorp TerraForm templates.

.. literalinclude:: ../static/config/manager-terraform-local.yaml
   :language: yaml

The metadata schema for Terraform manager:

.. literalinclude:: ../../../architect/schemas/terraform.yaml
   :language: yaml


References
----------

* https://www.terraform.io/docs/index.html
* https://github.com/terraform-providers
