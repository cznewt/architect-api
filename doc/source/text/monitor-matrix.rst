
================
Adjacency Matrix
================

An adjacency matrix is a square matrix used to represent a finite graph. The
elements of the matrix indicate whether pairs of vertices are adjacent or not
in the graph.

In the special case of a finite simple graph, the adjacency matrix is a
(0,1)-matrix with zeros on its diagonal. If the graph is undirected, the
adjacency matrix is symmetric. The relationship between a graph and the
eigenvalues and eigenvectors of its adjacency matrix is studied in spectral
graph theory.

The adjacency matrix should be distinguished from the incidence matrix for a
graph, a different matrix representation whose elements indicate whether
vertex–edge pairs are incident or not, and degree matrix which contains
information about the degree of each vertex.

.. figure:: ../static/img/monitor/adjacency-matrix.png
    :width: 100%
    :figclass: align-center

    Adjacency matrix of OpenStack project's resources (cca 100 nodes)


More Information
================

* https://github.com/micahstubbs/d3-adjacency-matrix-layout
* https://bl.ocks.org/micahstubbs/7f360cc66abfa28b400b96bc75b8984e (Micah Stubbs’s adjacency matrix layout)
* https://en.wikipedia.org/wiki/Adjacency_matrix
