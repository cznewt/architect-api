# -*- coding: utf-8 -*-

import json
from collections import OrderedDict
import six
from functools import update_wrapper
from django.contrib import messages
from django.conf import settings
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.base import RedirectView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator, classonlymethod
from django.contrib.auth.mixins import LoginRequiredMixin
from formtools.wizard.views import SessionWizardView
from architect.views import JSONDataView
from .models import Inventory, Resource
from .forms import InventoryDeleteForm, \
    ResourceDeleteForm, ResourceCreateForm
from .tasks import get_inventory_status_task, \
    sync_inventory_resources_task


class InventoryListView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/inventory_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inventory_list'] = Inventory.objects.order_by('name')
        return context


class InventoryCheckView(LoginRequiredMixin, RedirectView):
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


class InventorySyncView(LoginRequiredMixin, RedirectView):
    permanent = False
    pattern_name = 'inventory:inventory_detail'

    def get_redirect_url(self, *args, **kwargs):
        sync_inventory_resources_task.apply_async(
            (kwargs.get('inventory_name'),))
        return super().get_redirect_url(*args, **kwargs)


class InventoryDetailView(LoginRequiredMixin, TemplateView):
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


class InventoryDeleteView(LoginRequiredMixin, FormView):
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


class ResourceDetailView(LoginRequiredMixin, TemplateView):
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


class ResourceDeleteView(LoginRequiredMixin, FormView):
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

class ClassGenerateView(LoginRequiredMixin, FormView):
    template_name = "base_form.html"
    form_class = ResourceCreateForm

    def get_success_url(self):
        return reverse('inventory:inventory_list')

    def get_form_kwargs(self):
        inventory_name = self.kwargs.get('inventory_name')
        form_name = self.kwargs.get('form_name')
        inventory = Inventory.objects.get(name=inventory_name)
        form_meta = inventory.metadata['form'][form_name]['steps'][0]
        kwargs = super(ClassGenerateView, self).get_form_kwargs()
        kwargs.update({
            'inventory': inventory,
            'form_name': form_name,
            'form_meta': inventory.metadata['form'][form_name],
            'params': form_meta['fields']
        })
        return kwargs

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


class InventorySessionWizardView(SessionWizardView):

    @classmethod
    def get_initkwargs(cls, form_list=[], initial_dict=None, instance_dict=None,
                       condition_dict=None, *args, **kwargs):
        kwargs.update({
            'form_list': form_list,
            'initial_dict': (
                initial_dict or
                kwargs.pop('initial_dict', getattr(cls, 'initial_dict', None)) or {}
            ),
            'instance_dict': (
                instance_dict or
                kwargs.pop('instance_dict', getattr(cls, 'instance_dict', None)) or {}
            ),
            'condition_dict': (
                condition_dict or
                kwargs.pop('condition_dict', getattr(cls, 'condition_dict', None)) or {}
            )
        })
        return kwargs

    def set_form_list(self, request, *args, **kwargs):
        """
        Creates computed_form_list from the original form_list.
        Separated from the original `set_initkwargs` method.
        """
        # this will be created with some other magic later, now just hardcoded POC
        inventory_name = self.kwargs.get('inventory_name')
        form_name = self.kwargs.get('form_name')
        inventory = Inventory.objects.get(name=inventory_name)
        form_meta = inventory.metadata['form'][form_name]['steps'][0]
        print(kwargs)
        form_list = []

#        form_list = [('contact_form_1', ContactForm1), ('contact_form_2', ContactForm2)]

        computed_form_list = OrderedDict()

        # walk through the passed form list
        for i, form in enumerate(form_list):
            if isinstance(form, (list, tuple)):
                # if the element is a tuple, add the tuple to the new created
                # sorted dictionary.
                computed_form_list[six.text_type(form[0])] = form[1]
            else:
                # if not, add the form with a zero based counter as unicode
                computed_form_list[six.text_type(i)] = form

        # walk through the new created list of forms
        for form in six.itervalues(computed_form_list):
            if issubclass(form, formsets.BaseFormSet):
                # if the element is based on BaseFormSet (FormSet/ModelFormSet)
                # we need to override the form variable.
                form = form.form
            # check if any form contains a FileField, if yes, we need a
            # file_storage added to the wizardview (by subclassing).
            for field in six.itervalues(form.base_fields):
                if (isinstance(field, forms.FileField) and
                        not hasattr(cls, 'file_storage')):
                    raise NoFileStorageConfigured(
                        "You need to define 'file_storage' in your "
                        "wizard view in order to handle file uploads."
                    )

        self.form_list = computed_form_list

    def dispatch(self, request, *args, **kwargs):
        """
        This method gets called by the routing engine. The first argument is
        `request` which contains a `HttpRequest` instance.
        The request is stored in `self.request` for later use. The storage
        instance is stored in `self.storage`.
        After processing the request using the `dispatch` method, the
        response gets updated by the storage engine (for example add cookies).
        Override: construct `form_list` here and save it on view instance
        """
        self.set_form_list(request, *args, **kwargs)
        return super(GeneratedWizardView, self).dispatch(request, *args, **kwargs)


class ClassGenerateWizardView(InventorySessionWizardView):

    template_name = 'inventory/model_generate.html'

    def get_context_data(self, form, **kwargs):
        context = super(ClassGenerateWizardView, self).get_context_data(form=form, **kwargs)
        inventory_name = self.kwargs.get('inventory_name')
        form_name = self.kwargs.get('form_name')
        inventory = Inventory.objects.get(name=inventory_name)
        form_meta = inventory.metadata['form'][form_name]
        context.update({
            'inventory': inventory,
            'form_meta': form_meta
        })
        return context

    def done(self, form_list, **kwargs):
        return ""#HttpResponseRedirect(reverse_lazy('inventory:inventory_detail', kwargs['inventory_name']))
