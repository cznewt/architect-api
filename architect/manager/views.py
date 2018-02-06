# -*- coding: utf-8 -*-

from django.core.cache import cache
from django.conf import settings
from django.views.generic.base import TemplateView, RedirectView
from architect.views import JSONDataView
from architect.manager.models import Resource, Manager
from architect.manager.tasks import get_manager_status_task, \
    sync_manager_resources_task
from architect.manager.transform import transform_data, filter_node_types, \
    filter_lone_nodes, clean_relations


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


class ResourceDetailView(TemplateView):

    template_name = "manager/resource_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manager = Manager.objects.get(name=kwargs.get('manager_name'))
        resource_name = kwargs.get('resource_name')
        context['manager'] = manager
        context['resource'] = Resource.objects.get(manager=manager,
                                                   name=resource_name)
        return context
