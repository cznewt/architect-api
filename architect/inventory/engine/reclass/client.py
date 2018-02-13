# -*- coding: utf-8 -*-

import os
import re
import yaml
from collections import OrderedDict
from reclass import get_storage
from reclass.core import Core
from architect.inventory.client import BaseClient
from architect.inventory.models import Resource, Inventory
from celery.utils.log import get_logger

logger = get_logger(__name__)


class ReclassClient(BaseClient):

    def __init__(self, **kwargs):
        super(ReclassClient, self).__init__(**kwargs)

    def check_status(self):
        try:
            data = self.inventory()
            status = True
        except Exception:
            status = False
        return status

    def update_resources(self):
        inventory = Inventory.objects.get(name=self.name)
        for resource, metadata in self.inventory().items():
            res, created = Resource.objects.get_or_create(uid=resource,
                                                          inventory=inventory)
            if created:
                res.name = resource
                res.kind = 'reclass_node'
                res.metadata = metadata
                res.save()

    def inventory(self, resource=None):
        '''
        Get inventory nodes from reclass and their associated services
        and roles.
        '''
        storage = get_storage(self.metadata['storage_type'],
                              self.metadata['node_dir'],
                              self.metadata['class_dir'])
        reclass = Core(storage, None)
        if resource is None:
            return reclass.inventory()["nodes"]
        else:
            return reclass.inventory()["nodes"][resource]

    def class_list(self, resource=None):
        resource_list = {}
        for node_name, node in self.inventory().items():
            resource_list[node_name] = node['classes']
        if resource is None:
            return resource_list
        else:
            return {resource: resource_list[resource]}

    def parameter_list(self, resource=None):
        resource_list = {}
        for node_name, node in self.inventory().items():
            resource_list[node_name] = node['parameters']
        if resource is None:
            return resource_list
        else:
            return {resource: resource_list[resource]}

    def walk_raw_classes(self, ret_classes=True, ret_errors=False):
        '''
        Returns classes if ret_classes=True, else returns soft_params if
        ret_classes=False
        '''
        path = self.metadata['class_dir']
        classes = {}
        soft_params = {}
        errors = []

        # find classes
        for root, dirs, files in os.walk(path, followlinks=True):
            # skip hidden files and folders in reclass dir
            files = [f for f in files if not f[0] == '.']
            dirs[:] = [d for d in dirs if not d[0] == '.']
            # translate found init.yml to valid class name
            if 'init.yml' in files:
                class_file = root + '/' + 'init.yml'
                class_name = class_file.replace(path, '')[:-9].replace('/', '.')
                classes[class_name] = {'file': class_file}

            for f in files:
                if f.endswith('.yml') and f != 'init.yml':
                    class_file = root + '/' + f
                    class_name = class_file.replace(path, '')[:-4].replace('/', '.')
                    classes[class_name] = {'file': class_file}

        # read classes
        for class_name, params in classes.items():
            with open(params['file'], 'r') as f:
                # read raw data
                raw = f.read()
                pr = re.findall('\${_param:(.*?)}', raw)
                if pr:
                    params['params_required'] = list(set(pr))

                # load yaml
                try:
                    data = yaml.load(raw)
                except yaml.scanner.ScannerError as e:
                    errors.append(params['file'] + ' ' + str(e))
                    pass

                if type(data) == dict:
                    if data.get('classes'):
                        params['includes'] = data.get('classes', [])
                    if data.get('parameters') and data['parameters'].get('_param'):
                        params['params_created'] = data['parameters']['_param']

                    if not(data.get('classes') or data.get('parameters')):
                        errors.append(params['file'] + ' ' + 'file missing classes and parameters')
                else:
                    errors.append(params['file'] + ' ' + 'is not valid yaml')

        if ret_classes:
            return classes
        elif ret_errors:
            return errors

        # find parameters and its usage
        for class_name, params in classes.items():
            for pn, pv in params.get('params_created', {}).items():
                # create param if missing
                if pn not in soft_params:
                    soft_params[pn] = {'created_at': {}, 'required_at': []}

                # add created_at
                if class_name not in soft_params[pn]['created_at']:
                    soft_params[pn]['created_at'][class_name] = pv

            for pn in params.get('params_required', []):
                # create param if missing
                if pn not in soft_params:
                    soft_params[pn] = {'created_at': {}, 'required_at': []}

                # add created_at
                soft_params[pn]['required_at'].append(class_name)

        return soft_params

    def raw_class_list(self, prefix=None):
        '''
        Returns list of all classes defined in reclass inventory. You can
        filter returned classes by prefix.
        '''
        data = self.walk_raw_classes(ret_classes=True)
        return_data = {}
        for name, datum in data.items():
            name = name[1:]
            if prefix is None:
                return_data[name] = datum
            elif name.startswith(prefix):
                return_data[name] = datum
        return OrderedDict(sorted(return_data.items(), key=lambda t: t[0]))

    def raw_class_get(self, name):
        '''
        Returns detailes information about class file in reclass inventory.
        '''
        classes = self.raw_class_list()
        return {name: classes.get(name)}
