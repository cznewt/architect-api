# -*- coding: utf-8 -*-

from django.views.generic.base import TemplateView
from neomodel import db
from architect.manager.models import Resource, Manager
from architect.manager.tasks import get_manager_status_task


class ManagerListView(TemplateView):

    template_name = "manager/manager_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['manager_list'] = Manager.objects.all()
        return context


class ManagerDetailView(TemplateView):

    template_name = "manager/manager_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manager = Manager.objects.get(name=kwargs.get('manager_name'))
        host_list = Resource.objects.filter(manager=manager)
        context['manager'] = manager
        context['host_list'] = host_list

        return context


class ManagerScrapeView(TemplateView):

    template_name = "manager/host_detail.html"

    def get_context_data(self, **kwargs):
        get_manager_status_task.apply_async((kwargs.get('manager_name'),))


class HostDetailView(TemplateView):

    template_name = "manager/host_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_output = {}
        query = "match (n:salt_service)-[]-(m:salt_minion) where m.name='{}' return n".format(kwargs.get('host_name'))
        results, meta = db.cypher_query(query)
        service_list = [SaltMinionNode.inflate(row[0]) for row in results]
        for service in service_list:
            service_uid = '{}|{}'.format(kwargs.get('host_name'), service.name)
            query = "match (n:salt_lowstate)-[]-(m:salt_service) where m.uid='{}' and n.status='Unknown' return n".format(service_uid)
            results, meta = db.cypher_query(query)
            lowstate_unknown = [SaltLowstateNode.inflate(row[0]) for row in results]
            query = "match (n:salt_lowstate)-[]-(m:salt_service) where m.uid='{}' and n.status='Error' return n".format(service_uid)
            results, meta = db.cypher_query(query)
            lowstate_error = [SaltLowstateNode.inflate(row[0]) for row in results]
            query = "match (n:salt_lowstate)-[]-(m:salt_service) where m.uid='{}' and n.status='Active' return n".format(service_uid)
            results, meta = db.cypher_query(query)
            lowstate_active = [SaltLowstateNode.inflate(row[0]) for row in results]
            service_output[service.name] = {
                'lowstate_unknown': lowstate_unknown,
                'lowstate_error': lowstate_error,
                'lowstate_active': lowstate_active,
                'service': service
            }
        context['service_list'] = service_output
        context['host'] = SaltMinionNode.nodes.get(name=kwargs.get('host_name'))
        context['manager'] = kwargs.get('manager_name')

        return context


class ServiceDetailView(TemplateView):

    template_name = "manager/service_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_uid = '{}|{}'.format(kwargs.get('host_name'), kwargs.get('service_name'))
        query = "match (n:salt_lowstate)-[]-(m:salt_service) where m.uid='{}' return n".format(service_uid)
        results, meta = db.cypher_query(query)
        lowstate_list = [SaltServiceNode.inflate(row[0]) for row in results]
        context['lowstate_list'] = lowstate_list
        service_uid = '{}|{}'.format(kwargs.get('host_name'), kwargs.get('service_name'))
        context['service'] = SaltServiceNode.nodes.get(uid=service_uid)

        return context
