# -*- coding: utf-8 -*-

from datetime import timedelta
from django.core.cache import cache
from django.views.generic.base import TemplateView
from architect import utils
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
        output = {}
        monitor = Monitor.objects.get(name=kwargs.get('manager_name'))
        client_monitor = monitor.client()
        query = client_monitor._schema['query'].get(kwargs.get('query_name'))
        query_cache_key = '{}-{}'.format(monitor.name,
                                         kwargs.get('query_name'))
        client_monitor.queries = query['metric']
        output['query_cache_key'] = query_cache_key
        output['name'] = monitor.name
        outputs = []
        if 'start' in query:
            client_monitor.start = query['start']
            client_monitor.end = query['end']
            client_monitor.step = query['step']
            start_date = utils.get_date_object(query['start'])
            step_seconds = utils.unit_time_to_seconds(query['step'])
            data = client_monitor.get_range()
            x = ['x']
            if data is not None:
                data = data.to_dict('series')
                i = 0
                for series_name, series in data.items():
                    j = 0
                    list_series = []
                    for datum in series:
                        if i == 0:
                            start_offset = j * timedelta(seconds=step_seconds)
                            date_object = start_date + start_offset
                            x.append(date_object.strftime('%Y-%m-%d %H:%M:%S'))
                            j += 1
                        list_series.append(datum)
                    i += 1
                    outputs.append([series_name, ] + list_series)
            else:
                data = {}
            outputs = [x] + outputs
        else:
            client_monitor.moment = query['moment']
            data = client_monitor.get_instant()
            if data is not None:
                data = data.to_dict('series')
                i = 0
                for series_name, series in data.items():
                    list_series = []
                    for datum in series:
                        list_series.append(datum)
                    i += 1
                    outputs.append([series_name, ] + list_series)
            else:
                data = {}
        output['data'] = outputs
        return output
