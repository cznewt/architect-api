# -*- coding: utf-8 -*-

import yaml
from django.http import HttpResponse
from django.views import View
from architect.inventory.engine.reclass import inventory


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


class GetHostDataView(View):

    def get(self, request, *args, **kwargs):
        node_list = inventory(kwargs.get('master_id'))
        node = node_list[kwargs.get('minion_id')]
        node.pop('__reclass__')
        if '_param' in node.get('parameters'):
            node.get('parameters').pop('_param')
        return HttpResponse(yaml.dump(node.get('parameters')))
