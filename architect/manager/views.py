# -*- coding: utf-8 -*-

from django.views.generic.base import TemplateView, RedirectView
from architect.manager.models import Resource, Manager
from architect.manager.tasks import get_manager_status_task


class ManagerListView(TemplateView):

    template_name = "manager/manager_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['manager_list'] = Manager.objects.order_by('name')
        return context


class ManagerCheckView(RedirectView):

    permanent = False
    query_string = True
    pattern_name = 'manager:manager_list'

    def get_redirect_url(self, *args, **kwargs):
        managers = Manager.objects.all()
        for manager in managers:
            if manager.client().check_status():
                manager.status = 'active'
            else:
                manager.status = 'error'
            manager.save()
        return super().get_redirect_url(*args, **kwargs)


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


class ManagerUpdateView(RedirectView):

    permanent = False
    pattern_name = 'manager:manager_detail'

    def get_redirect_url(self, *args, **kwargs):
        get_manager_status_task.apply_async((kwargs.get('manager_name'),))
        return super().get_redirect_url(*args, **kwargs)


class ResourceDetailView(TemplateView):

    template_name = "manager/resource_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manager = Manager.objects.get(name=kwargs.get('manager_name'))
        kind = manager.get_schema()['default_resource']
        context['manager'] = manager
        context['resource'] = Resource.objects.get(manager=manager,
                                                   uid=kwargs.get('resource_name'))
        return context
