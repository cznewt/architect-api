# -*- coding: utf-8 -*-

import json
from django.urls import reverse
from django.http import HttpResponse
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.base import RedirectView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from architect.views import JSONDataView
from .models import Inventory
from .forms import SaltFormulasInventoryCreateForm, InventoryDeleteForm


class InventoryListView(TemplateView):

    template_name = "inventory/inventory_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inventory_list'] = Inventory.objects.order_by('name')
        return context


class InventoryCheckView(RedirectView):

    permanent = False
    query_string = True
    pattern_name = 'inventory:inventory_list'

    def get_redirect_url(self, *args, **kwargs):
        inventories = Inventory.objects.all()
        for inventory in inventories:
            if inventory.client().check_status():
                inventory.status = 'active'
            else:
                inventory.status = 'error'
            inventory.save()
        return super().get_redirect_url(*args, **kwargs)


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
        return inventory.inventory()


class InventoryCreateView(FormView):
    template_name = "inventory/inventory_update.html"
    form_class = SaltFormulasInventoryCreateForm
    success_url = '/inventory/v1'
    initial = {
        'classes_dir': '/srv/salt/reclass/classes',
        'nodes_dir': '/srv/salt/reclass/nodes',
        'formulas_dir': '/srv/salt/env/prd'
    }

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


class InventoryDeleteView(FormView):
    template_name = "inventory/inventory_delete.html"
    form_class = InventoryDeleteForm
    success_url = '/inventory/v1'

    def get_success_url(self):
        return reverse('inventory:inventory_list')

    def get_form_kwargs(self):
        inventory_name = self.kwargs.get('inventory_name')
        kwargs = super(InventoryDeleteView, self).get_form_kwargs()
        kwargs.update({'initial': {'inventory_name': inventory_name}})
        return kwargs

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


class InventoryCreateJSONView(JSONDataView):

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


class ResourceCreateView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ResourceCreateView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse('Only POST method is supported.')

    def post(self, request, *args, **kwargs):
        metadata = json.loads(request.body.decode("utf-8"))
        manager_kwargs = {
            'name': kwargs.get('master_id'),
            'engine': 'saltstack',
        }
        update_client = SaltStackClient(**manager_kwargs)
        metadata['manager'] = kwargs.get('master_id')
        update_client.process_resource_metadata('salt_event', metadata)
        cache_client = SaltStackClient(**manager_kwargs)
        cache_client.refresh_cache()
        return HttpResponse('OK')
