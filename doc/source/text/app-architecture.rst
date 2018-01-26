
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

.. figure:: ../static/scheme/high_level_arch.png
    :width: 80%
    :align: center

    High-level achitecture of Architect system


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
