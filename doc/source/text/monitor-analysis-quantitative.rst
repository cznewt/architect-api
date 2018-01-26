
=====================
Quantitative Analysis
=====================

With the relational information we are now able to corellate resources and
joined topologies from varius information sources. This gives you the real
power, while having the underlying relational structure, you can gather
unstructured metrics, events, alarms and put them into proper context in you
managed resources.

The metrics collected from you infrastrucute can be assigned to various
vertices and edges in your network. This can give you more insight to the
utilisation of depicted infrastructures.

You can have the following query to the prometheus server that gives you the
rate of error response codes goint through a HAproxy for example.

.. code-block:: yaml

    sum(irate(haproxy_http_response_5xx{
        proxy=~"glance.*",
        sv="FRONTEND"
    }[5m]))

Or you can have the query with the same result to the InfluxDB server:

.. code-block:: yaml

    SELECT sum("count")
        FROM "openstack_glance_http_response_times"
        WHERE "hostname" =~ /$server/
            AND "http_status" = '5xx'
            AND $timeFilter
        GROUP BY time($interval)
    fill(0)

Having these metrics you can assign numerical properties of your relational
nodes with these values and use them in correct context.
