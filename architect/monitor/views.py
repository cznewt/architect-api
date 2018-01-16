# -*- coding: utf-8 -*-

from django.views.generic.base import TemplateView
from architect.views import JSONDataView
from architect.manager.models import Manager
from architect.monitor.models import Monitor
from architect.monitor.transform import default_graph


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
        manager_client = Manager.objects.get(name=widget['data_source']
                                                        ['default']
                                                        ['manager']).client()
        manager_client.load_resources()
        # manager_client.load_relations()
        data = default_graph(manager_client.to_dict())
        data['name'] = widget.get('name', kwargs.get('widget_name'))
        return data
