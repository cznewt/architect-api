# -*- coding: utf-8 -*-

from django.core.cache import cache
from django.views.generic.base import TemplateView
from architect.views import JSONDataView
from architect.monitor.models import Monitor


class MonitorListView(TemplateView):

    template_name = "monitor/monitor_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['monitor_list'] = Monitor.objects.order_by('name')
        return context


class MonitorDetailView(TemplateView):

    template_name = "monitor/monitor_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        monitor = Monitor.objects.get(name=kwargs.get('monitor_name'))
        context['monitor'] = monitor
        return context


class MonitorQueryJSONView(JSONDataView):

    def get_context_data(self, **kwargs):
        data = {}
        monitor = Monitor.objects.get(name=kwargs.get('manager_name'))
        client_monitor = monitor.client()
        query = client_monitor._schema['query'].get(kwargs.get('query_name'))
        query_cache_key = '{}-{}'.format(monitor.name,
                                         kwargs.get('query_name'))
        if 'step' in query:
            client_monitor.start = query['start']
            client_monitor.end = query['end']
            client_monitor.step = query['step']
        else:
            client_monitor.instant = query['instant']
        client_monitor.queries = query['metric']

        data['query_cache_key'] = query_cache_key
        data['name'] = monitor.name
        range_data = client_monitor.get_range()
        if range_data is not None:
            data['data'] = range_data.to_dict('series')
        else:
            data['data'] = {}
        return data
