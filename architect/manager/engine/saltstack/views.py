# -*- coding: utf-8 -*-

import json
import yaml
from django.conf import settings
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from neomodel.core import DoesNotExist
from architect.inventory.engine.reclass import inventory
from architect.manager.models import registry

SaltMasterNode = registry.get_type('salt_master')
SaltMinionNode = registry.get_type('salt_minion')
SaltServiceNode = registry.get_type('salt_service')
SaltLowstateNode = registry.get_type('salt_lowstate')


def _get_or_create_salt_minion(minion_name, master, metadata={}):
    try:
        minion_node = SaltMinionNode.nodes.get(uid=minion_name)
    except DoesNotExist:
        minion_kwargs = {
            'uid': minion_name,
            'kind': 'salt_minion',
            'name': minion_name,
            'metadata': metadata
        }
        minion_node = SaltMinionNode(**minion_kwargs)
        minion_node.save()
        relation = minion_node.master.build_manager(minion_node, 'master')
        relation.connect(master, {})
    return minion_node


def _get_or_create_salt_service(service_name, minion, metadata={}):
    uid = '{}|{}'.format(minion.name, service_name)
    try:
        service_node = SaltServiceNode.nodes.get(uid=uid)
    except DoesNotExist:
        service_kwargs = {
            'uid': uid,
            'kind': 'salt_service',
            'name': service_name,
            'metadata': metadata
        }
        service_node = SaltServiceNode(**service_kwargs)
        service_node.save()
        relation = service_node.minion.build_manager(service_node, 'minion')
        relation.connect(minion, {})
    return service_node


def _get_or_create_salt_lowstate(minion, service, metadata={}):
    uid = '{}|{}'.format(minion.name, metadata['__id__'])
    try:
        lowstate_node = SaltLowstateNode.nodes.get(uid=uid)
    except DoesNotExist:
        lowstate_kwargs = {
            'uid': uid,
            'kind': 'salt_lowstate',
            'name': metadata['__id__'],
            'metadata': metadata
        }
        lowstate_node = SaltLowstateNode(**lowstate_kwargs)
        lowstate_node.save()
        relation = service.lowstate.build_manager(service, 'lowstate')
        relation.connect(lowstate_node, {})
    return lowstate_node


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
        data = json.loads(request.body.decode("utf-8"))
        print(yaml.dump(data))
        for datum_name, datum in data['return'].items():
            print(datum)
            uid = '{}|{}'.format(data['id'], datum['__id__'])
            lowstate = SaltLowstateNode.nodes.get_or_none(uid=uid)
            to_save = False
            if lowstate is not None:
                if 'apply' not in lowstate.metadata:
                    lowstate.metadata['apply'] = []
                    lowstate.metadata['apply'].append(datum)
                    if datum['result']:
                        lowstate.status = 'Active'
                    else:
                        lowstate.status = 'Error'
                    to_save = True
                else:
                    if lowstate.metadata['apply'][-1]['result'] != datum['result']:
                        lowstate.metadata['apply'].append(datum)
                        if datum['result']:
                            lowstate.status = 'Active'
                        else:
                            lowstate.status = 'Error'
                        to_save = True
            if to_save:
                lowstate.save()
        return HttpResponse('OK')


class ProcessGrainView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ProcessGrainView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return HttpResponse('Only POST method is supported.')

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode("utf-8"))
        master_name = kwargs.get('master_id')
        master = SaltMasterNode.nodes.get(uid=master_name)
        for minion_name, minion_data in data.items():
            minion = _get_or_create_salt_minion(minion_name, master)
            if isinstance(minion_data, dict):
                minion.metadata = minion_data
                minion.status = 'Active'
            minion.save()
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
        data = json.loads(request.body.decode("utf-8"))
        master_name = kwargs.get('master_id')
        master = SaltMasterNode.nodes.get(uid=master_name)
        for minion_name, minion_data in data.items():
            minion = _get_or_create_salt_minion(minion_name, master)
            try:
                for minion_datum in minion_data:
                    minion = _get_or_create_salt_minion(minion_name, master)
                    service_key_parts = minion_datum['__sls__'].split('.')
                    service_key = '{}-{}'.format(service_key_parts[0],
                                                 service_key_parts[1])
                    service = _get_or_create_salt_service(service_key, minion, {})
                    lowstate = _get_or_create_salt_lowstate(minion,
                                                            service,
                                                            minion_datum)
            except TypeError:
                pass
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
        data = json.loads(request.body.decode("utf-8"))
        master_name = kwargs.get('master_id')
        master = SaltMasterNode.nodes.get(uid=master_name)
        for minion_name, minion_data in data.items():
            minion = _get_or_create_salt_minion(minion_name, master)
            try:
                for service_name, service in minion_data.items():
                    if service_name not in settings.RECLASS_SERVICE_BLACKLIST:
                        for role_name, role in service.items():
                            if role_name not in settings.RECLASS_ROLE_BLACKLIST:
                                service_key = '{}-{}'.format(service_name,
                                                             role_name)
                                _get_or_create_salt_service(service_key,
                                                            minion,
                                                            role)
            except AttributeError:
                pass
        return HttpResponse('OK')
