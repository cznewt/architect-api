# -*- coding: utf-8 -*-

import json
import yaml
from django.conf import settings
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from neomodel.core import DoesNotExist
from architect.manager.engine.saltstack.client import SaltStackClient


class GetInventoryView(View):

    def get(self, request, *args, **kwargs):
        node_list = inventory(kwargs.get('master_id'))
        result = {}

        for node_name, node in node_list.items():
            service_class = []
            role_class = []
            for service_name, service in node['parameters'].items():
                if service_name not in service_black_list:
                    service_class.append(service_name)
                    for role_name, role in service.items():
                        if role_name not in role_black_list:
                            role_class.append('{}.{}'.format(service_name,
                                                             role_name))
            result[node_name] = {
                'roles': role_class,
                'services': service_class,
            }
        return HttpResponse(yaml.dump(result))


class GetNodePillarView(View):

    def get(self, request, *args, **kwargs):
        node_list = inventory(kwargs.get('master_id'))
        node = node_list[kwargs.get('minion_id')]
        node.pop('__reclass__')
        if '_param' in node.get('parameters'):
            node.get('parameters').pop('_param')
        return HttpResponse(yaml.dump(node.get('parameters')))


class GetNodeTopView(View):

    def get(self, request, *args, **kwargs):
        node_list = inventory(kwargs.get('master_id'))
        node = node_list[kwargs.get('minion_id')]
        return HttpResponse(yaml.dump(node.get('applications')))


class ProcessEventView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ProcessEventView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse('Only POST method is supported.')

    def post(self, request, *args, **kwargs):
        metadata = json.loads(request.body.decode("utf-8"))
        manager_client = SaltStackClient(**{
            'name': kwargs.get('master_id'),
            'engine': 'saltstack',
        })
        manager_client.process_resource_metadata('salt_event', metadata)
        manager_client.save()
        return HttpResponse('OK')


class ProcessGrainView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ProcessGrainView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse('Only POST method is supported.')

    def post(self, request, *args, **kwargs):
        metadata = json.loads(request.body.decode("utf-8"))
        manager_client = SaltStackClient(**{
            'name': kwargs.get('master_id'),
            'engine': 'saltstack',
        })
        manager_client.process_resource_metadata('salt_minion', metadata)
        manager_client.save()
        return HttpResponse('OK')


class ProcessLowstateView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ProcessLowstateView, self).dispatch(request,
                                                         *args,
                                                         **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse('Only POST method is supported.')

    def post(self, request, *args, **kwargs):
        metadata = json.loads(request.body.decode("utf-8"))
        manager_client = SaltStackClient(**{
            'name': kwargs.get('master_id'),
            'engine': 'saltstack',
        })
        manager_client.process_resource_metadata('salt_lowstate', metadata)
        manager_client.save()
        return HttpResponse('OK')


class ProcessPillarView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ProcessPillarView, self).dispatch(request,
                                                       *args,
                                                       **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse('Only POST method is supported.')

    def post(self, request, *args, **kwargs):
        metadata = json.loads(request.body.decode("utf-8"))
        manager_client = SaltStackClient(**{
            'name': kwargs.get('master_id'),
            'engine': 'saltstack',
        })
        manager_client.process_resource_metadata('salt_service', metadata)
        manager_client.save()
        return HttpResponse('OK')
