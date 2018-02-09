
=======================
Salt inventory consumer
=======================

To enable Salt Master inventory, you need to install ``http_architect`` Pillar
and Top modules and add following to the Salt Master configuration files. To
support the grains.

.. code-block:: yaml

    http_architect: &http_architect
      project: local-salt
      host: architect.service.host
      port: 8181

    ext_pillar:
      - http_architect: *http_architect

    master_tops:
      http_architect: *http_architect
