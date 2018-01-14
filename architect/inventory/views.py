# -*- coding: utf-8 -*-

from django.conf import settings
from django.views.generic.base import TemplateView
from architect.inventory.engine.reclass import inventory
from architect.inventory.models import Inventory


class InventoryListView(TemplateView):

    template_name = "inventory/inventory_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inventory_list'] = Inventory.objects.all()
        return context


class InventoryDetailView(TemplateView):

    template_name = "inventory/inventory_detail.html"

    def get_context_data(self, **kwargs):
        name = kwargs.get('inventory_name')
        node_list = inventory(name)
        context = super().get_context_data(**kwargs)
        context['inventory'] = Inventory.objects.get(name=name)
        context['node_list'] = {}
        for node_name, node in node_list.items():
            role_class = []
            for service_name, service in node['parameters'].items():
                if service_name not in settings.RECLASS_SERVICE_BLACKLIST:
                    for role_name, role in service.items():
                        if role_name not in settings.RECLASS_ROLE_BLACKLIST:
                            role_class.append('{}-{}'.format(service_name,
                                                             role_name))
            context['node_list'][node_name] = role_class
        return context


class HostDetailView(TemplateView):

    template_name = "inventory/host_detail.html"

    def get_context_data(self, **kwargs):
        inventory_name = kwargs.get('inventory_name')

        node_list = inventory(inventory_name)
        context = super().get_context_data(**kwargs)
        context['inventory'] = Inventory.objects.get(name=inventory_name)
        context['node_list'] = {}

        for node_name, node in node_list.items():
            role_class = []
            for service_name, service in node['parameters'].items():
                if service_name not in settings.RECLASS_SERVICE_BLACKLIST:
                    for role_name, role in service.items():
                        if role_name not in settings.RECLASS_ROLE_BLACKLIST:
                            role_class.append('{}-{}'.format(service_name,
                                                             role_name))
            context['node_list'][node_name] = role_class
        return context
