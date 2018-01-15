# -*- coding: utf-8 -*-

from django.views.generic.base import TemplateView
from architect.views import JSONDataView
from .models import Inventory

class InventoryListView(TemplateView):

    template_name = "inventory/inventory_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inventory_list'] = Inventory.objects.all()
        return context


class InventoryDetailView(TemplateView):

    template_name = "inventory/inventory_detail.html"

    def get_context_data(self, **kwargs):
        inventory = Inventory.objects.get(name=kwargs.get('inventory_name'))
        context = super().get_context_data(**kwargs)
        context['inventory'] = inventory
        context['resource_list'] = inventory.class_list()
        if inventory.status != 'active' and len(context['resource_list']) > 0:
            inventory.status = 'active'
            inventory.save()
        return context


class InventoryDetailJSONView(JSONDataView):

    def get_context_data(self, **kwargs):
        inventory = Inventory.objects.get(name=kwargs.get('inventory_name'))
        # context = super().get_context_data(**kwargs)
        return inventory.inventory()


class ResourceDetailView(TemplateView):

    template_name = "inventory/resource_detail.html"

    def get_context_data(self, **kwargs):
        inventory = Inventory.objects.get(name=kwargs.get('inventory_name'))
        context = super().get_context_data(**kwargs)
        context['inventory'] = inventory
        context['resource_name'] = kwargs.get('resource_name')
        resource_list = inventory.class_list()
        context['class_list'] = resource_list[context['resource_name']]
        return context


class ResourceDetailJSONView(JSONDataView):

    def get_context_data(self, **kwargs):
        inventory = Inventory.objects.get(name=kwargs.get('inventory_name'))
        # context = super().get_context_data(**kwargs)
        return inventory.inventory(kwargs.get('resource_name'))
