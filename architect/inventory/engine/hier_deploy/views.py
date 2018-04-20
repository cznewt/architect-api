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
from .forms import InventoryCreateForm, NodeCreateForm, NodeUpdateForm, \
    ParamCreateForm, ParamUpdateForm, ParamDeleteForm
from architect.inventory.models import Inventory, Resource


class NodeDetailView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/node_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inventory'] = Inventory.objects.get(name=kwargs.pop('inventory_name'))
        context['node'] = Resource.objects.get(name=kwargs.pop('node_name'),
                                               inventory=context['inventory'])
        return context


class NodeCreateView(LoginRequiredMixin, FormView):
    template_name = "base_form.html"
    form_class = NodeCreateForm
    success_url = '/success'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.kwargs)
        return kwargs

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


class NodeUpdateView(LoginRequiredMixin, FormView):
    template_name = "base_form.html"
    form_class = NodeUpdateForm
    success_url = '/success'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.kwargs)
        return kwargs

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


class ParamCreateView(LoginRequiredMixin, FormView):
    template_name = "base_form.html"
    form_class = ParamCreateForm
    success_url = '/success'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.kwargs)
        return kwargs

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


class ParamUpdateView(LoginRequiredMixin, FormView):
    template_name = "base_form.html"
    form_class = ParamUpdateForm
    success_url = '/success'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.kwargs)
        return kwargs

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


class ParamDeleteView(LoginRequiredMixin, FormView):
    template_name = "base_form.html"
    form_class = ParamDeleteForm
    success_url = '/success'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(self.kwargs)
        return kwargs

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


class InventoryCreateView(LoginRequiredMixin, FormView):
    template_name = "base_form.html"
    form_class = InventoryCreateForm
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
        form = InventoryCreateForm(inventory_kwargs)
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
