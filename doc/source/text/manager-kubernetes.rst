
===================
Kubernetes Clusters
===================

Kubernetes requires some information from ``kubeconfig`` file. You provide the
parameters of the cluster and the user to the manager. These can be found
under corresponding keys in the kubernetes configuration file.

.. literalinclude:: ../static/config/manager-kubernetes.yaml
   :language: yaml

.. note::

    Options ``config.cluster`` and ``config.user`` can be found in your
    ``kubeconfig`` file. Just copy the config fragment with cluster parameters
    and fragment with user parameter.
