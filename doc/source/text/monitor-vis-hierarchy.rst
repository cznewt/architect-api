
===========================
Hierarchical Visualizations
===========================

Tree graphs are frequently drawn as ``node-link diagrams`` in which the vertices
are represented as disks, boxes, or textual labels and the edges are
represented as line segments, polylines, or curves in the Euclidean plane.

Node-link diagrams can be traced back to the 13th century work of Ramon Llull,
who drew diagrams of this type for complete graphs in order to analyze all
pairwise combinations among sets of metaphysical concepts.


Dendrograms
===========

Dendrograms are node-link diagrams that place leaf nodes of the tree at the
same depth. Dendograms are typically less compact than tidy trees, but are
useful when all the leaves should be at the same level, such as for
hierarchical clustering or phylogenetic tree diagrams.

.. figure:: ../static/img/monitor/node-link-tree.png
    :width: 80%
    :figclass: align-center

    SaltStack services in Hierarchical edge bundle


Partition Layouts
=================

The partition layout produces adjacency diagrams: a space-filling variant of a
node-link tree diagram. Rather than drawing a link between parent and child in
the hierarchy, nodes are drawn as solid areas (either arcs or rectangles), and
their placement relative to other nodes reveals their position in the
hierarchy. The size of the nodes encodes a quantitative dimension that would
be difficult to show in a node-link diagram.

.. figure:: ../static/img/monitor/sunburst.png
    :width: 80%
    :figclass: align-center

    SaltStack services in Sunburst Diagram


Circle Packing
==============

We display resources as circles with lower-level resources as inner circles.
Circle packing in a circle is a two-dimensional packing problem with the
objective of packing unit circles into the smallest possible larger circle.

.. figure:: ../static/img/monitor/circle-packing.png
    :width: 80%
    :figclass: align-center

    SaltStack services in Circle Packing
