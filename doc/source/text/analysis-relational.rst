
========================
Relational Data Analysis
========================

You can analyse the resource models in several ways. Either you want to get
the subsets of the resources (vertices and edges) or you want to combine
multiple graphs and link the same nodes in each.


Relational Schema
=================

All resources are covered by schema that define basic properties of the nodes
and relationships.


Resource Nodes
--------------

Sample node definition of the OpenStack hypervisor resource. We declare
directional typed relationships at either side by ``relationship_to`` and
``relationship_from`` parameters.

.. code-block:: yaml

    os_hypervisor:
      resource: OS::Nova::Hypervisor
      client: nova
      name: Hypervisor
      icon: fa:server  
      model:
        aggregate:
          type: relationship_to
          model: in_os_aggregate
          target: os_aggregate


Resource Relations
------------------

Along the node definition we define the relations.

.. code-block:: yaml

    on_os_hypervisor:
      relation:
        os_server: hypervisor
        os_port: hypervisor
    in_os_aggregate:
      relation:
        os_hypervisor: aggregate


Relational Operations
=====================

We can either break a body of information down into smaller parts or to
examine it from different viewpoints that we can understand it better and we
can also combine multiple bodies in one get further insight.

Subgraphs - Slicing and Dicing
------------------------------

To slice and dice is to break a body of information down into smaller parts or
to examine it from different viewpoints that we can understand it better.

In cooking, you can slice a vegetable or other food or you can dice it (which
means to break it down into small cubes). One approach to dicing is to first
slice and then cut the slices up into dices.

.. code-block:: yaml

    name: Hive-plot
    data_source:
      default:
        manager: openstack-project
        layout: graph
        filter_node_types:
        - os_server
        - os_key_pair
        - os_flavor
        - os_network
        - os_subnet
        - os_floating_ip
        - os_router
        filter_lone_nodes:
        - os_key_pair
        - os_flavor


In data analysis, the term generally implies a systematic reduction of a body
of data into smaller parts or views that will yield more information. The term
is also used to mean the presentation of information in a variety of different
and useful ways. In our case we find useful subgraphs of the infrastructures.


Hiearchical Structures
----------------------

In some cases it is useful to crate hierarchical structures from graph data.
For example in OpenStack infrastructure we can show the ``aggregate zone`` -
``hypervisor`` - ``instance`` relations and show the quantitative properties
of hypervisors and instances. The properties can be used RAM or CPU, runtime -
the age of resources or any other property of value.

.. code-block:: yaml

    name: Tree Structure (aggregate zone > hypervisor > instance)
    height: 1
    chart: tree
    data_source:
      default:
        manager: openstack-region
        layout: hierarchy
        hierarchy_layers:
          0:
            name: Region1
            kind:
          1:
            kind: os_aggregate_zone
          2:
            kind: os_hypervisor
            target: in_os_aggregate_zone
          3:
            kind: os_server
            target: on_os_hypervisor

Another example would be filtering of resources by tenant or stack
attributions. This reduces the number of nodes to the reasonable amount.


Inter-graphs
------------

On other hand you want to combine several graphs to create one overlaying
graph. This is very useful to combine in other ways undelated resources. For
example we can say that ``OpenStack Server`` or ``AWS Instance`` and ``Salt
Minion`` are really the same resources.

.. code-block:: yaml

    name: Hive-plot
    data_source:
      default:
        manager: openstack-project
        layout: graph
        filter_node_types:
        - os_server
