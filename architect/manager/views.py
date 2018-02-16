# -*- coding: utf-8 -*-

import json
from django.core.cache import cache
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import FormView
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from architect.views import JSONDataView
from .forms import ManagerActionForm, ResourceActionForm
from .models import Resource, Manager
from .tasks import get_manager_status_task, \
    sync_manager_resources_task
from .transform import transform_data, filter_node_types, \
    filter_lone_nodes, clean_relations
from architect.document.models import Document


class ManagerListView(TemplateView):

    template_name = "manager/manager_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['manager_list'] = Manager.objects.order_by('name')
        return context


class ManagerDetailView(TemplateView):

    template_name = "manager/manager_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manager = Manager.objects.get(name=kwargs.get('manager_name'))
        kind = manager.get_schema()['default_resource']
        context['manager'] = manager
        context['workflow_options'] = manager.client()._schema['resource'][kind].get('workflow')
        context['resource_list'] = Resource.objects.filter(manager=manager,
                                                           kind=kind)
        return context


class ManagerCheckView(RedirectView):

    permanent = False
    query_string = True
    pattern_name = 'manager:manager_list'

    def get_redirect_url(self, *args, **kwargs):
        managers = Manager.objects.all()
        for manager in managers:
            get_manager_status_task.apply_async((manager.name,))
        return super().get_redirect_url(*args, **kwargs)


class ManagerActionView(FormView):

    template_name = "manager/manager_action.html"
    form_class = ManagerActionForm
    success_url = '/success'

    def get_form_kwargs(self):
        manager = Manager.objects.get(name=self.kwargs.get('manager_name'))
        kwargs = super(ManagerActionView, self).get_form_kwargs()
        print(self.kwargs.get('resource_kind'))
        print(self.kwargs.get('resource_action'))
        kwargs.update({
            'resource_kind': self.kwargs.get('resource_kind'),
            'resource_action': self.kwargs.get('resource_action'),
            'manager_name': manager.name,
            'params': manager.client().get_action_fields(self.kwargs.get('resource_kind'),
                                                         self.kwargs.get('resource_action'))
        })
        return kwargs

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


class ManagerCreateJSONView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ManagerCreateJSONView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse('Only POST method is supported.')

    def post(self, request, *args, **kwargs):
        metadata = json.loads(request.body.decode("utf-8"))
        current_managers = Manager.objects.filter(name=metadata.get('manager_name'))
        if current_managers.count() > 0:
            return JsonResponse({'error': "Manager with name '{}' already exists.".format(metadata.get('manager_name'))})
        manager_kwargs = {
            'name': metadata.get('manager_name'),
            'engine': 'saltstack',
            'metadata': {
                "auth_url": metadata.get('manager_url'),
                "password": metadata.get('manager_password'),
                "username": metadata.get('manager_user')
            }
        }
        manager = Manager(**manager_kwargs)
        if manager.client().check_status():
            manager.status = 'active'
        else:
            manager.status = 'error'
        manager.save()
        document_name = manager.name
        widget_name = '02-manager-resources'
        widget_meta = {
            'name': 'SaltStack resources',
            'update_interval': 5,
            'width': 'col-sm-6 col-md-6 mb-3',
            'height': 1,
            'chart': 'sunburst',
            'data_source': {
                'default': {
                    'type': 'relational',
                    'source': manager.name,
                    'query': 'salt_minion_lowstates_tree',
                }
            }
        }
        document, created = Document.objects.get_or_create(name=document_name)
        if created:
            document.metadata = {'widget': {}}
            document.save()
        document.add_widget(widget_name, widget_meta)
        document.save()

        status = {'success': "Manager '{}' was created.".format(metadata.get('manager_name'))}
#        status = {'failure': 'Inventory form validation failed: {}.'.format(errors)}
        return JsonResponse(status)


class ManagerSyncView(RedirectView):

    permanent = False
    pattern_name = 'manager:manager_detail'

    def get_redirect_url(self, *args, **kwargs):
        sync_manager_resources_task.apply_async((kwargs.get('manager_name'),))
        return super().get_redirect_url(*args, **kwargs)


class ManagerQueryJSONView(JSONDataView):

    def get_context_data(self, **kwargs):
        manager = Manager.objects.get(name=kwargs.get('manager_name'))
        query = manager.client()._schema['query'].get(kwargs.get('query_name'))
        manager_cache_key = manager.name
        query_cache_key = '{}-{}'.format(manager.name,
                                         kwargs.get('query_name'))
        layout = query.get('layout', 'graph')
        raw_data = cache.get(manager_cache_key)
        if raw_data is None:
            manager_client = manager.client()
            manager_client.load_resources()
            manager_client.load_relations()
            raw_data = manager_client.to_dict()
            cache.set(manager_cache_key,
                      raw_data,
                      settings.RESOURCE_CACHE_DURATION)
            print('Saved manager cache {}'.format(manager_cache_key))
        else:
            print('Loaded manager cache {}'.format(manager_cache_key))
        data = cache.get(query_cache_key)
        if data is None:
            if layout == 'graph':
                transform = 'default_graph'
                options = {}
                data = transform_data(raw_data, transform, options)
                if query.get('filter_node_types', []):
                    data = filter_node_types(data,
                                             query.get('filter_node_types'))
                if query.get('filter_lone_nodes', []):
                    data = filter_lone_nodes(data,
                                             query.get('filter_lone_nodes'))
                data = clean_relations(data)
            elif layout == 'hierarchy':
                transform = 'default_hier'
                options = query.get('hierarchy_layers', {})
                data = transform_data(raw_data, transform, options)
            cache.set(query_cache_key,
                      data,
                      settings.RESOURCE_CACHE_DURATION)
            print('Saved manager query cache {}'.format(query_cache_key))
        else:
            print('Loaded manager query cache {}'.format(query_cache_key))
        data['name'] = manager.name
        return data


class ResourceActionView(FormView):

    template_name = "base_form.html"
    form_class = ResourceActionForm

    def get_success_url(self):
        kwargs = {
            'manager_name': self.kwargs.get('manager_name'),
            'resource_uid': self.kwargs.get('resource_uid'),
            'resource_action': self.kwargs.get('resource_action')
        }
        action_url = reverse('form_success')
        return action_url

    def get_form_kwargs(self):
        manager = Manager.objects.get(name=self.kwargs.get('manager_name'))
        resource = Resource.objects.get(manager=manager,
                                        uid=self.kwargs.get('resource_uid'))
        action = self.kwargs.get('resource_action')
        kwargs = super(ResourceActionView, self).get_form_kwargs()
        kwargs.update({
            'manager': manager,
            'resource': resource,
            'action': action,
            'params': manager.client().get_resource_action_fields(resource,
                                                                  action)
        })
        return kwargs

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


class ResourceDetailView(TemplateView):

    template_name = "manager/resource_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manager = Manager.objects.get(name=kwargs.get('manager_name'))
        resource_uid = kwargs.get('resource_uid')
        context['manager'] = manager
        context['resource'] = Resource.objects.get(manager=manager,
                                                   id=resource_uid)
        return context
