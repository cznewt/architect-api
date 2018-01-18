
=================
Architect Monitor
=================

``Graph drawing`` or ``network diagram`` is a pictorial representation of the
vertices and edges of a graph. This drawing should not be confused with the
graph itself, very different layouts can correspond to the same graph. In the
abstract, all that matters is which pairs of vertices are connected by edges.
In the concrete, however, the arrangement of these vertices and edges within a
drawing affects its understandability, usability, fabrication cost, and
aesthetics.

The problem gets worse, if the graph changes over time by adding and deleting
edges (dynamic graph drawing) and the goal is to preserve the user's mental
map.


Conventions
===========

Graphs are frequently drawn as ``node-link diagrams`` in which the vertices
are represented as disks, boxes, or textual labels and the edges are
represented as line segments, polylines, or curves in the Euclidean plane.

Node-link diagrams can be traced back to the 13th century work of Ramon Llull,
who drew diagrams of this type for complete graphs in order to analyze all
pairwise combinations among sets of metaphysical concepts.

.. toctree::
   :maxdepth: 2

   monitor-arc.rst
   monitor-bundle.rst
   monitor-force.rst
   monitor-hive.rst
   monitor-matrix.rst
