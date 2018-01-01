# -*- coding: utf-8 -*-

from django.views.generic.base import TemplateView
from django.conf import settings


class ManagerListView(TemplateView):

    template_name = "manager/manager_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manager_list = []
        for manager_name, manager_item in settings.MANAGER_ENGINES.items():
            manager_list.append({
                'name': manager_name,
                'engine': manager_item['engine'],
                'status': 'OK'
            })

        context['manager_list'] = manager_list
        return context


class ManagerDetailView(TemplateView):

    template_name = "manager/manager_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manager = settings.MANAGER_ENGINES[kwargs.get('name')]
        manager['name'] = kwargs.get('name')
        context['manager'] = manager
        return context
