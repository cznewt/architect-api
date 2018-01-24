
=====================
The Architect Project
=====================


The aim of this project is to provide unified service modeling, management and
visualization platform agnostic of delivery method. It creates virtual
representations of any software services or physical resources and allows
control over their entire life-cycle. The name of project comes from Architect
program in Matrix movie series:

    In the Matrix the Architect is a highly specialized, humorless program of
    the machine world as well as the creator of the Matrix. As the chief
    administrator of the system, he is possibly a collective manifestation, or
    at the very least a virtual representation of the entire Machine
    mainframe.

The Architect service consists of several core compontents:

Inventory Component
    Inventory is the Architect's metadata engine. It encapsulates and unifies data
    from various metadata sources to provide inventory/metadata for various
    orchestration services.

Manager Component
    Manager is the Architect's orchestration engine. The aim of this module is
    to enforce infrastructure topologies models and acquire live
    infrastructure topology data from any resource provider for further
    relational and quantitative analysis and visualisations.

Monitor Component
    The structure of infrastructure resources is directed graph that can be
    subject for further analysis. We can perform several transformation
    functions on this graph data in Monitor component.

Following figure shows high-level achitecture of Architect system.

.. figure:: ./doc/source/static/scheme/high_level_arch.png
    :align: center
    :width: 80%


Architect Documentation
=======================

Installation instructions, getting started guides, and API documentation.

https://architect-api.readthedocs.io/


Architect Components
====================

A quick summary of integrations and capabilities of individual modules.


Inventory Component
-------------------

Inventory is the Architect's metadata engine. It encapsulates and unifies data
from various metadata sources to provide inventory/metadata for various
orchestration services. Currently supported metadata engines are:

* reclass (python3 version)

The following inventory providers are to be intergrated in near future.

* hiera
* saltstack

There is a plan to integrate workflow (multi-step forms) defitions to simplify
creation of complex infrastructure models.


Manager Component
-----------------

Manager is the Architect's orchestration engine. The aim of this module is to
enforce infrastructure topologies models and acquire live infrastructure
topology data from any resource provider for further relational and
quantitative analysis and visualisations.

The pull approach for querying endpoint APIs is supported at the moment, the
processing push from target services is supported for SaltStack events.
Currently supported resource providers are:

* Kubernetes clusters
* OpenStack clouds
* Amazon web services
* SaltStack infrastructures
* Terraform templates
* Jenkins pipelines

The following resource providers are to be intergrated in near future.

* GCE and Azure clouds
* Cloudify TOSCA blueprints
* JUJU templates


Monitor Component
-----------------

The structure of infrastructure resources is directed graph that can be
subject for further analysis. We can perform several transformation functions
on this graph data in Monitor component.

Currently supported relational analysis visualizations:

* Adjacency Matrix
* Arc Diagram
* Force-directed Layouts
* Hierarchical Edge Bundling
* Hive Plot
* Node-link Trees (Reingold-Tilford, Dendrograms)
* Partition Layouts (Sunburst, Icicle Diagrams, Treemaps)


Installation
============

Following steps show how to deploy various components of the Architect service
and connections to external services.


Service architect-api Installation
----------------------------------

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

Following configuration for individual inventories/managers/models can be
stored in config files or in the database.


Architect Inventory Configuration
---------------------------------

Each manager endpoint expects different configuration. Following samples show
the required parameters to setup individual invetory backends.


Reclass (Inventory Backend)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Following configuration points to the reclass inventory storage on local
filesystem.

.. code-block:: yaml

    class_dir: /srv/salt/reclass/classes
    node_dir: /srv/salt/reclass/nodes
    storage_type: yaml_fs
    filter_keys:
      - _param


Architect Manager Configuration
-------------------------------

Each manager endpoint expects different configuration. Following samples show
the required parameters to setup each endpoint type.


Amazon Web Services (Manager Endpoint)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

AWS manager uses ``boto3`` high level AWS python SDK for accessing and
manipulating with AWS resources.


.. code-block:: yaml

    region: us-west-2
    aws_access_key_id: {{ access_key_id }}
    aws_secret_access_key: {{ secret_access_key }}


Kubernetes (Manager Endpoint)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Kubernetes requires some information from ``kubeconfig`` file. You provide the
parameters of the cluster and the user to the manager. These can be found
under corresponding keys.

.. code-block:: yaml

    scope: global
    cluster:
      certificate-authority-data: |
        {{ ca-for-server-and-clients }}
      server: https://{{ kubernetes-api }}:443
    user:
      client-certificate-data: |
        {{ client-cert-public }}
      client-key-data: |
        {{ client-cert-private }}

.. note::

    Options ``config.cluster`` and ``config.user`` can be found in your
    ``kubeconfig`` file. Just copy the config fragment with cluster parameters
    and fragment with user parameter.


OpenStack (Manager Endpoint)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration for keystone ``v2.0`` and keystone ``v3`` clouds. Configuration
sample for single tenant access.

.. code-block:: yaml

    scope: local
    region_name: RegionOne
    compute_api_version: '2.1'
    auth:
      username: {{ user-name }}
      password: {{ user-password }}
      project_name: {{ project-name }}
      domain_name: 'default'
      auth_url: https://{{ keystone-api }}:5000/v3

Config for managing resources of entire cloud, including hypervisors, tenants,
etc in given region.

.. code-block:: yaml

    scope: global
    region_name: RegionOne
    auth:
      username: {{ admin-name }}
      password: {{ admin-password }}
      project_name: admin
      auth_url: https://{{ keystone-api }}:5000/v2.0


SaltStack (Manager Endpoint)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration for manager connection to Salt API.

.. code-block:: yaml

    auth_url: http://{{ salt-api }}:8000
    username: {{ user-name }}
    password: {{ user-password }}

Following figure shows how SaltStack integrates with Architect Inventory and
Manager. Please note that you can use Inventory intergration independetly of
the Manager intergration.

.. figure:: ./doc/source/static/scheme/manager_salt.png
    :align: center
    :width: 60%


Terraform (Manager Endpoint)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration for parsing Hashicorp Terraform templates.

.. code-block:: yaml

    dir: ~/terraform/{{ terraform-dir }}


Architect Monitor Configuration
-------------------------------

Following config snippets show configuration for supported types of
visualization. Currently we support Network graphs, hierarchical structures
for quatitative analysis.


Network Graphs
~~~~~~~~~~~~~~

The manager endpoint is used as source of relational data. The data can be
sliced and diced as shown in the example.

.. code-block:: yaml

    name: Hive-plot
    chart: hive
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


Hiearchical Structures
~~~~~~~~~~~~~~~~~~~~~~

The manager endpoint is used as source of relational data. This data can be
traversed to create hiearchies. The hierarchical data has it's own family of
visualization techniques.

.. code-block:: yaml

    name: Tree Structure (cluster > namespace > pod > service)
    height: 1
    chart: tree
    data_source:
      default:
        manager: k8s-demo
        layout: hierarchy
        hierarchy_layers:
          0:
            name: Kubernetes Root
            kind:
          1:
            kind: k8s_namespace
          2:
            kind: k8s_pod
            target: in_k8s_namespace
          3:
            kind: k8s_service
            target: in_k8s_pod


Architect Client Installation
-----------------------------

Managers that do not expose any form of API can be controlled locally by using
architect-adapter worker that wrap the local orchestration engine (Ansible,
Cloudify, TerraForm).


Salt Master (Inventory Integration)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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


Salt Master (Manager Integration)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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


Data Visualization
==================

Different data require different diagram visualization. Diagrams are symbolic
representation of information according to some visualization technique. Every
time you need to emphasise different qualities of displayed resources you can
choose from several layouts to display the data.


Relational Layouts
------------------


Network Graph Layouts
~~~~~~~~~~~~~~~~~~~~~

For most of the cases we will be dealing with network data that do not have
any single root or beginning.


Force-Directed Graph
^^^^^^^^^^^^^^^^^^^^

`Force-directed graph` drawing algorithms are used for drawing graphs in an
aesthetically pleasing way. Their purpose is to position the nodes of a graph
in two-dimensional or three-dimensional space so that all the edges are of
more or less equal length and there are as few crossing edges as possible, by
assigning forces among the set of edges and the set of nodes, based on their
relative positions, and then using these forces either to simulate the motion
of the edges and nodes or to minimize their energy.

.. figure:: ./doc/source/static/img/monitor/force-directed-graph.png
    :width: 100%
    :figclass: align-center

    Kubernetes cluster in Force-directed graph


Hive Plot
^^^^^^^^^

The `hive plot` is a visualization method for drawing networks. Nodes
are mapped to and positioned on radially distributed linear axes — this
mapping is based on network structural properties. Edges are drawn as curved
links. Simple and interpretable.

.. figure:: ./doc/source/static/img/monitor/hive-plot.png
    :width: 100%
    :figclass: align-center

    Kubernetes cluster in Hive plot


Arc Diagram
^^^^^^^^^^^

An `arc diagram` is a style of graph drawing, in which the vertices of a graph
are placed along a line in the Euclidean plane, with edges being drawn as
semicircles in one of the two halfplanes bounded by the line, or as smooth
curves formed by sequences of semicircles. In some cases, line segments of the
line itself are also allowed as edges, as long as they connect only vertices
that are consecutive along the line.

.. figure:: ./doc/source/static/img/monitor/arc-diagram.png
    :width: 100%
    :figclass: align-center

    Arc diagram of OpenStack project's resources (cca 100 resources)


Adjacency Matrix
^^^^^^^^^^^^^^^^

An adjacency matrix is a square matrix used to represent a finite graph. The
elements of the matrix indicate whether pairs of vertices are adjacent or not
in the graph.

.. figure:: ./doc/source/static/img/monitor/adjacency-matrix.png
    :width: 100%
    :figclass: align-center

    Adjacency matrix of OpenStack project's resources (cca 100 resources)


Hierarchical Edge Bundling
^^^^^^^^^^^^^^^^^^^^^^^^^^

Danny Holten presents an aesthetically pleasing way of simplifying graphs and
making tree graphs more accessible. What makes his project so useful, however,
is how he outlines the particular thought process that goes into making a
visualization.

.. figure:: ./doc/source/static/img/monitor/hiearchical-edge-bundling.png
    :width: 100%
    :figclass: align-center

    SaltStack services in Hierarchical edge bundle


Tree Graph Layouts
~~~~~~~~~~~~~~~~~~

Directed graph traversal can give os acyclic structures suitable for showing
parent-child relations in your subraphs.


Dendrograms
^^^^^^^^^^^

Dendrograms are node-link diagrams that place leaf nodes of the tree at the
same depth. Dendograms are typically less compact than tidy trees, but are
useful when all the leaves should be at the same level, such as for
hierarchical clustering or phylogenetic tree diagrams.

.. figure:: ./doc/source/static/img/monitor/node-link-tree.png
    :width: 100%
    :figclass: align-center

    SaltStack services in Hierarchical edge bundle


Partition Layouts
^^^^^^^^^^^^^^^^^

The partition layout produces adjacency diagrams: a space-filling variant of a
node-link tree diagram. Rather than drawing a link between parent and child in
the hierarchy, nodes are drawn as solid areas (either arcs or rectangles), and
their placement relative to other nodes reveals their position in the
hierarchy. The size of the nodes encodes a quantitative dimension that would
be difficult to show in a node-link diagram.

.. figure:: ./doc/source/static/img/monitor/sunburst.png
    :width: 100%
    :figclass: align-center

    SaltStack services in Sunburst Diagram


Circle Packing
^^^^^^^^^^^^^^

We display resources as circles with lower-level resources as inner circles.
Circle packing in a circle is a two-dimensional packing problem with the
objective of packing unit circles into the smallest possible larger circle.

.. figure:: ./doc/source/static/img/monitor/circle-packing.png
    :width: 100%
    :figclass: align-center

    SaltStack services in Circle Packing

