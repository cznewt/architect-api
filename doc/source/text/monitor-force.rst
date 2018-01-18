
====================
Force-Directed Graph
====================

`Force-directed graph` drawing algorithms are used for drawing graphs in an
aesthetically pleasing way. Their purpose is to position the nodes of a graph
in two-dimensional or three-dimensional space so that all the edges are of
more or less equal length and there are as few crossing edges as possible, by
assigning forces among the set of edges and the set of nodes, based on their
relative positions, and then using these forces either to simulate the motion
of the edges and nodes or to minimize their energy.

While graph drawing can be a difficult problem, force-directed algorithms,
being physical simulations, usually require no special knowledge about graph
theory such as planarity.

Good-quality results can be achieved for graphs of medium size (up to 50–500
vertices), the results obtained have usually very good results based on the
following criteria: uniform edge length, uniform vertex distribution and
showing symmetry. This last criterion is among the most important ones and is
hard to achieve with any other type of algorithm.


Sample Visualizations
=====================

.. figure:: ../static/img/monitor/force-directed-plot.png
    :width: 600px
    :figclass: align-center

    Force-directed plot of all OpenStack resources (cca 3000 nodes)


More Information
================

* https://en.wikipedia.org/wiki/Force-directed_graph_drawing
* https://bl.ocks.org/shimizu/e6209de87cdddde38dadbb746feaf3a3 (shimizu’s D3 v4 - force layout)
* https://bl.ocks.org/mbostock/3750558 (Mike Bostock’s Sticky Force Layout)
* https://bl.ocks.org/emeeks/302096884d5fbc1817062492605b50dd (D3v4 Constraint-Based Layout)
