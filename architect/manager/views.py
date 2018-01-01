# -*- coding: utf-8 -*-

from django.conf import settings
from django.views.generic.base import TemplateView
from neomodel import db
from architect.manager.models import registry

SaltMasterNode = registry.get_type('salt_master')
SaltMinionNode = registry.get_type('salt_minion')
SaltServiceNode = registry.get_type('salt_service')
SaltLowstateNode = registry.get_type('salt_lowstate')


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
        manager = settings.MANAGER_ENGINES[kwargs.get('manager_name')]
        manager['name'] = kwargs.get('manager_name')
        context['manager'] = manager
        salt_master = SaltMasterNode.nodes.get(name=kwargs.get('manager_name'))
        salt_minion = SaltMinionNode.nodes.all()
        context['salt_master'] = salt_master

        query = "match (n:salt_minion)-[]-(m:salt_master) where m.name='{}' return n".format(kwargs.get('manager_name'))
        results, meta = db.cypher_query(query)
        host_list = [SaltMinionNode.inflate(row[0]) for row in results]
        context['host_list'] = host_list

        return context


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
