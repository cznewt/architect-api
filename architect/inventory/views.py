# -*- coding: utf-8 -*-

import json
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.base import RedirectView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from architect.views import JSONDataView
from .models import Inventory, Resource
from .forms import HierDeployInventoryCreateForm, InventoryDeleteForm, \
    ResourceDeleteForm
from .tasks import get_inventory_status_task, \
    sync_inventory_resources_task


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
            get_inventory_status_task.apply_async((inventory.name,))
        messages.add_message(self.request,
                             messages.SUCCESS,
                             'Finished syncing of inventories.')
        return super().get_redirect_url(*args, **kwargs)


class InventorySyncView(RedirectView):

    permanent = False
    pattern_name = 'inventory:inventory_detail'

    def get_redirect_url(self, *args, **kwargs):
        sync_inventory_resources_task.apply_async(
            (kwargs.get('inventory_name'),))
        return super().get_redirect_url(*args, **kwargs)


class InventoryDetailView(TemplateView):

    template_name = "inventory/inventory_detail.html"

    def get_context_data(self, **kwargs):
        inventory = Inventory.objects.get(name=kwargs.get('inventory_name'))
        context = super().get_context_data(**kwargs)
        context['inventory'] = inventory
        if inventory.engine == 'hier-cluster':
            context['service_formula_list'] = Resource.objects.filter(
                inventory=inventory,
                kind='service_formula')
            context['service_class_list'] = Resource.objects.filter(
                inventory=inventory,
                kind='service_class')
            context['system_unit_list'] = Resource.objects.filter(
                inventory=inventory,
                kind='system_unit')
            context['system_class_list'] = Resource.objects.filter(
                inventory=inventory,
                kind='system_class')
            context['cluster_class_list'] = Resource.objects.filter(
                inventory=inventory,
                kind='cluster_class')
            context['cluster_unit_list'] = Resource.objects.filter(
                inventory=inventory,
                kind='cluster_unit')
        return context


class InventoryDetailJSONView(JSONDataView):

    def get_context_data(self, **kwargs):
        inventory = Inventory.objects.get(name=kwargs.get('inventory_name'))
        return inventory.inventory()


class InventoryCreateView(FormView):

    template_name = "base_form.html"
    form_class = HierDeployInventoryCreateForm
    success_url = '/success'
    initial = {
        'classes_dir': '/srv/salt/reclass/classes',
        'nodes_dir': '/srv/salt/reclass/nodes',
    }

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


class InventoryCreateJSONView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(InventoryCreateJSONView, self).dispatch(
            request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse('Only POST method is supported.')

    def post(self, request, *args, **kwargs):
        metadata = json.loads(request.body.decode("utf-8"))
        current_inventories = Inventory.objects.filter(
            name=metadata.get('inventory_name'))
        if current_inventories.count() > 0:
            return JsonResponse({'error': "Inventory with name '{}' already exists.".format(metadata.get('inventory_name'))})
        inventory_kwargs = {
            'cluster_domain': metadata.get('domain_name'),
            'cluster_name': metadata.get('cluster_name'),
            'inventory_name': metadata.get('inventory_name'),
            'class_dir': settings.INVENTORY_RECLASS_CLASSES_DIRS[0][0],
        }
        print(inventory_kwargs)
        form = HierDeployInventoryCreateForm(inventory_kwargs)
        if form.is_valid():
            form.handle()
            status = {'success': "Inventory '{}' was created.".format(metadata.get('inventory_name'))}
        else:
            errors = []
            for error in form.non_field_errors():
                errors.append(error)
            for field in form:
                for error in field.errors:
                    errors.append('{}: {}'.format(field.name, error))
            status = {'failure': 'Inventory form validation failed: {}.'.format(errors)}
        return JsonResponse(status)


class InventoryDeleteView(FormView):

    template_name = "base_form.html"
    form_class = InventoryDeleteForm
    success_url = '/inventory/v1/success'

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


class ResourceDetailView(TemplateView):

    template_name = "inventory/resource_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inventory = Inventory.objects.get(name=kwargs.get('inventory_name'))
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


class ResourceDeleteView(FormView):

    template_name = "base_form.html"
    form_class = ResourceDeleteForm
    success_url = '/inventory/v1/success'

    def get_success_url(self):
        return reverse('inventory:inventory_list')

    def get_form_kwargs(self):
        inventory_name = self.kwargs.get('inventory_name')
        resource_name = self.kwargs.get('resource_name')
        kwargs = super(ResourceDeleteView, self).get_form_kwargs()
        kwargs.update({'initial': {
            'inventory_name': inventory_name,
            'resource_name': resource_name
        }})
        return kwargs

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


class ResourceClassifyView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ResourceClassifyView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse('Only POST method is supported.')

    def post(self, request, *args, **kwargs):
        metadata = json.loads(request.body.decode("utf-8"))
        manager_kwargs = {
            'name': kwargs.get('master_id'),
            'engine': 'saltstack',
        }
        return HttpResponse('OK')
