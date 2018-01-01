# -*- coding: utf-8 -*-

from django.conf import settings
from django.views.generic.base import TemplateView
from architect.inventory.engine.reclass import inventory


class InventoryListView(TemplateView):

    template_name = "inventory/inventory_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inventory_list = []
        for inventory_name, inventory_item in settings.INVENTORY_ENGINES.items():
            if inventory_item['engine'] == 'reclass':
                node_list = inventory(inventory_name)
                inventory_list.append({
                    'name': inventory_name,
                    'engine': inventory_item['engine'],
                    'nodes': len(node_list),
                    'status': 'Active'
                })
            else:
                inventory_list.append({
                    'name': inventory_name,
                    'engine': inventory_item['engine'],
                    'nodes': 0,
                    'status': 'Error'
                })
        context['inventory_list'] = inventory_list
        return context


class InventoryDetailView(TemplateView):

    template_name = "inventory/inventory_detail.html"

    def get_context_data(self, **kwargs):
        node_list = inventory(kwargs.get('inventory_name'))
        context = super().get_context_data(**kwargs)
        context['node_list'] = {}
        inventory_item = settings.INVENTORY_ENGINES[kwargs.get('inventory_name')]
        inventory_item['name'] = kwargs.get('inventory_name')

        for node_name, node in node_list.items():
            role_class = []
            for service_name, service in node['parameters'].items():
                if service_name not in settings.RECLASS_SERVICE_BLACKLIST:
                    for role_name, role in service.items():
                        if role_name not in settings.RECLASS_ROLE_BLACKLIST:
                            role_class.append('{}-{}'.format(service_name,
                                                             role_name))
            context['node_list'][node_name] = role_class

        context['inventory'] = inventory_item
        return context


class HostDetailView(TemplateView):

    template_name = "inventory/host_detail.html"

    def get_context_data(self, **kwargs):
        node_list = inventory(kwargs.get('inventory_name'))
        context = super().get_context_data(**kwargs)
        context['node_list'] = {}
        inventory_item = settings.INVENTORY_ENGINES[kwargs.get('inventory_name')]
        inventory_item['name'] = kwargs.get('inventory_name')

        for node_name, node in node_list.items():
            role_class = []
            for service_name, service in node['parameters'].items():
                if service_name not in settings.RECLASS_SERVICE_BLACKLIST:
                    for role_name, role in service.items():
                        if role_name not in settings.RECLASS_ROLE_BLACKLIST:
                            role_class.append('{}-{}'.format(service_name,
                                                             role_name))
            context['node_list'][node_name] = role_class

        context['inventory'] = inventory_item
        return context
