
=========================
Cloud Resource Management
=========================

Amazon Web Services
===================

AWS manager uses ``boto3`` high level AWS python SDK for accessing and
manipulating AWS resources.

.. literalinclude:: ../static/config/manager-amazon.yaml
   :language: yaml

The metadata schema for AWS manager:

.. literalinclude:: ../../../architect/schemas/amazon.yaml
   :language: yaml


OpenStack Cloud Resources
=========================

Configuration for keystone ``v2.0`` and keystone ``v3`` clouds. Configuration
sample for single tenant access.

.. literalinclude:: ../static/config/manager-openstack-project.yaml
   :language: yaml
   :emphasize-lines: 1

Config for managing resources of entire cloud, including hypervisors, tenants,
etc in given region.

.. literalinclude:: ../static/config/manager-openstack-region.yaml
   :language: yaml
   :emphasize-lines: 1

The metadata schema for OpenStack manager:

.. literalinclude:: ../../../architect/schemas/openstack.yaml
   :language: yaml
