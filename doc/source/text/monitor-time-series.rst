
======================
Time-series Monitoring
======================

Monitor components can query metrics from several time-series databases into
uniform Pandas DataFrames.

It support two types of metric queries, the first is ``instant`` metric,
returning the value in precise moment in time. The second is the ``range``
metric, giving you the series of values for given time range and step.


The Monitor supports several major time-series databases to get the
results in normalised way. The endpoints are queried thru HTTP API calls.


Graphite Time-series Database
=============================

Example configuration for the Graphite server.

.. literalinclude:: ../static/config/monitor-graphite.yaml
   :language: yaml

Example query to the Graphite server.

.. code-block:: none

    averageSeries(server.web*.load)


References
----------

* http://graphite.readthedocs.io/en/latest/render_api.html


InfluxDb Time-series Database
=============================

Example configuration for the InfluxDb server.

.. literalinclude:: ../static/config/monitor-influxdb.yaml
   :language: yaml

Example query to the InfluxDb server.

.. code-block:: none

    SELECT mean("value") FROM "alertmanager_notifications_total"


References
----------

* https://docs.influxdata.com/influxdb/v1.3/guides/querying_data/


Prometheus Server
=================

Example configuration for the Prometheus server.

.. literalinclude:: ../static/config/monitor-prometheus.yaml
   :language: yaml

Example query to the Prometheus server.

.. code-block:: none

    alertmanager_notifications_total


References
----------

* https://prometheus.io/docs/prometheus/latest/querying/api/
* https://github.com/infinityworks/prometheus-example-queries
