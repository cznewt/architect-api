
======================
Architect Introduction
======================

The aim of this project is to provide unified service modeling, management and
visualization platform agnostic of delivery or orchestration method. It
creates virtual representations of any software services or physical resources
and allows control over crucial steps in their life cycle. Both reductionist
and holistic approaches are used to descibe target systems. The project name
comes from Architect program in Matrix movie series:

    In the Matrix the Architect is a highly specialized, humorless program of
    the machine world as well as the creator of the Matrix. As the chief
    administrator of the system, he is possibly a collective manifestation, or
    at the very least a virtual representation of the entire Machine
    mainframe.

The The Architect project was started as part of my thesis "Visualization of
cloud performace metrics". Now we explore the possible implications of
combining the relational models of infrastructures with quantitative data that
relates to it. This the implementation of holistic approach to the IT system
modeling. You combine the capabilities of the brain (inventory), muscles
(manager) and senses (monitor) to create the full body of IT system. This
vague analogy, but you seldom see all the parts of infrastrucure working
together as one, the source of truth providing the vital information to the
orchestration engines and configuring the monitoring to reflect the actual
state. Then you can start implementing your policy engines and machine
learching techiques to improve the state of your initial models. This is not
possible to achieve withnout proper decomposition your system to individual
pieces but also you need to put it back together and look at it as whole.


The Project History
===================

Academic research in particular fields has been undergoing since 2013. We have
published series of research papers covering in detail specificic areas of
capabilities that became part of Architect project.

In 2014 we got published *Security information and event management in the
cloud computing infrastructure* and presented at CINTI 2014 - 15th IEEE
International Symposium on Computational Intelligence and Informatics,
Proceedings.

In 2015 we got published *Opensource automation in cloud computing* at Lecture
Notes in Electrical Engineering and *Network visualization survey* at Lecture
Notes in Computer Science (including subseries Lecture Notes in Artificial
Intelligence and Lecture Notes in Bioinformatics).

Also *High level models for IaaS cloud architectures* published at Studies in
Computational Intelligence and *Measurement of cloud computing services
availability* published in Lecture Notes of the Institute for Computer
Sciences, Social-Informatics and Telecommunications Engineering, LNICST made
in year 2015.

In 2017 we got published *Hybrid system orchestration with TOSCA and salt* in
Journal of Engineering and Applied Sciences and *VNF orchestration and
modeling with ETSI MANO compliant frameworks* which got published at Lecture
Notes in Computer Science (including subseries Lecture Notes in Artificial
Intelligence and Lecture Notes in Bioinformatics).

We tried to identify possible options to model cloud architectures,
ontologies, definition hiearchies. The good, the bad and the ugly of metadata.
Then we focused on ways to manage orchestration processes, not only for
compute servers but also for virtual network resources. Some works focuced on
measuring cloud metrics and evaluating log event data important to undestand
the types of data the systems emit and how to normalise these to consitent
domains. And last type of works, some of them unpublished, were concerned with
the visualization layout methods, transformation techniques for relational and
quatitative data. The individual reseach papers were focusec on gaining
expertise in given domain. The Architect project wraps the outcome of
individual research into consistent holistic framework for modeling complete
IT infrastructures.


PhD Thesis Abstract
===================

This thesis provides implementation of platform for holistic system modeling.
It tries to define the main components of system governance, that are required
for autonomous long-term opertations and interactions. These components are
the brain, source of truth that provides models to the muscles and senses. The
orchestration platforms or cloud service providers are the virtual muscles.
The senses are the tools that create and process the metrics and event data.
Usually sences are backed by multiple levels of human powered support teams.
The proposed platform allows combination of brain, muscles and senses to
create entity which can displayes in different perspectives by well tailored
visualizations that reflect the actual life-cycle state of the governed
infrastructures.

The main part of work presents implementation of Architect project, that has
been developed as proof-of-concept implementation of holistic governance
system capable of modern user and systems interactions. It can display service
relations and gathered metrics and give advanced insight to important Cloud
computing performance qualities. Modern systems rely closely on cloud and
virtualisation architectures. To optimize utilization of resources,
applications and infrastructure must not be controlled separately.

We propose a united platform that can discribe major orchestration engines and
monitoring solutions in common schema, create metadata inventories that can
provide proper context to any of these services. On top of this infrastructure
models, you have powerful interfactive visualizations that can be used to
display properties of interest. On other side the models of actual
infrastructure states are good entrypoint for further machine assisted
analysis and learning techniques.


Keywords
--------

Cloud Computing, Metadata, Virtualization, Metering, Monitoring, SOA, Data
Transformation, Data Visualization, Chart, Time-series, Event, Holism, Service
Science, System Science


Resources
---------

* Documentation: https://architect-api.readthedocs.io/en/latest/
* API source: https://github.com/cznewt/architect-api
* Client source: https://github.com/cznewt/architect-client
* Research papers: https://www.scopus.com/authid/detail.uri?authorId=56501819000
