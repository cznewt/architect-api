# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.cache import cache
from django.views.generic.base import TemplateView
from architect.views import JSONDataView
from architect.manager.models import Manager
from architect.monitor.models import Monitor
from architect.monitor.transform import transform_data, filter_node_types, \
    filter_lone_nodes, clean_relations


class MonitorListView(TemplateView):

    template_name = "monitor/monitor_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['monitor_list'] = Monitor.objects.all()
        return context


class MonitorDetailView(TemplateView):

    template_name = "monitor/monitor_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        monitor = Monitor.objects.get(name=kwargs.get('monitor_name'))
        context['monitor'] = monitor
        return context


class WidgetDetailView(TemplateView):

    template_name = "monitor/widget_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        monitor = Monitor.objects.get(name=kwargs.get('monitor_name'))
        context['monitor'] = monitor
        return context


class WidgetDetailJSONView(JSONDataView):

    def get_context_data(self, **kwargs):
        monitor = Monitor.objects.get(name=kwargs.get('monitor_name'))
        widget = monitor.widgets()[kwargs.get('widget_name')]
        data_source = widget['data_source']['default']
        manager_key = data_source['manager']
        layout = data_source.get('layout', 'graph')
        raw_data = cache.get(manager_key)
        if raw_data is None:
            manager_client = Manager.objects.get(name=manager_key).client()
            manager_client.load_resources()
            manager_client.load_relations()
            raw_data = manager_client.to_dict()
            cache.set(manager_key, raw_data, settings.RESOURCE_CACHE_DURATION)
            print('Saved key {} to cache'.format(manager_key))
        else:
            print('Loaded key {} from cache'.format(manager_key))
        for typum, datum in raw_data['resources'].items():
            print('{}: {}'.format(typum, len(datum)))
        for typum, datum in raw_data['relations'].items():
            print('{}: {}'.format(typum, len(datum)))
        if layout == 'graph':
            transform = 'default_graph'
            options = {}
            data = transform_data(raw_data, transform, options)
            if data_source.get('filter_node_types', []):
                data = filter_node_types(data,
                                         data_source.get('filter_node_types'))
            if data_source.get('filter_lone_nodes', []):
                data = filter_lone_nodes(data,
                                         data_source.get('filter_lone_nodes'))
            data = clean_relations(data)
        elif layout == 'hierarchy':
            transform = 'default_hier'
            options = data_source.get('hierarchy_layers', {})
            data = transform_data(raw_data, transform, options)
        data['name'] = widget.get('name', kwargs.get('widget_name'))
        return data
