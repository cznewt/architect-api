# -*- coding: utf-8 -*-

import os
import re
import yaml
import glob
import six
from string import Template
import docutils
from collections import OrderedDict
from django.conf import settings
from reclass import get_storage
from reclass.core import Core
from architect import utils
from architect.inventory.client import BaseClient
from architect.inventory.models import Resource, Inventory
from celery.utils.log import get_logger

logger = get_logger(__name__)


class HierDeployClient(BaseClient):

    def __init__(self, **kwargs):
        super(HierDeployClient, self).__init__(**kwargs)

    def check_status(self):
        try:
            self.inventory()
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
        Get inventory nodes from reclass salt formals and their
        associated services and roles.
        '''
        storage = get_storage('yaml_fs',
                              self.metadata['node_dir'],
                              self.metadata['class_dir'])
        reclass = Core(storage, None)
        if resource is None:
            return reclass.inventory()["nodes"]
        else:
            return reclass.inventory()["nodes"][resource]

    def parameter_list(self, resource=None):
        resource_list = {}
        return resource_list

    def class_list(self, resource=None):
        resource_list = {}
        for node_name, node in self.inventory().items():
            role_class = []
            for service_name, service in node['parameters'].items():
                if service_name not in settings.RECLASS_SERVICE_BLACKLIST:
                    for role_name, role in service.items():
                        if role_name not in settings.RECLASS_ROLE_BLACKLIST:
                            role_class.append('{}-{}'.format(service_name,
                                                             role_name))
            resource_list[node_name] = role_class
        if resource is None:
            return resource_list
        else:
            return {resource: resource_list[resource]}

    def resource_create(self, name, metadata):
        file_name = '{}/{}.yml'.format(self.metadata['node_dir'], name)
        with open(file_name, 'w+') as file_handler:
            yaml.safe_dump(metadata, file_handler, default_flow_style=False)

    def resource_delete(self, name):
        file_name = '{}/{}.yml'.format(self.metadata['node_dir'], name)
        os.remove(file_name)
        inventory = Inventory.objects.get(name=self.name)
        resource = Resource.objects.get(inventory=inventory, name=name)
        resource.delete()

    def save_override_param(self, name, value):
        file_name = '{}/overrides/{}.yml'.format(self.metadata['class_dir'],
                                                 self.name.replace('.', '-'))
        inventory = Inventory.objects.get(name=self.name)
        inventory.cache['overrides'][name] = value
        inventory.save()
        metadata = {
            'parameters': {
                '_param': inventory.cache['overrides']
            }
        }
        with open(file_name, 'w+') as file_handler:
            yaml.safe_dump(metadata, file_handler, default_flow_style=False)

    def init_overrides(self):
        file_name = '{}/overrides/{}.yml'.format(self.metadata['class_dir'],
                                                 self.name.replace('.', '-'))
        if 'cluster_name' not in self.metadata:
            return
        metadata = {
            'parameters': {
                '_param': {
                    'cluster_name': self.metadata['cluster_name'],
                    'cluster_domain': self.metadata['cluster_domain']
                }
            }
        }
        with open(file_name, 'w+') as file_handler:
            yaml.safe_dump(metadata, file_handler, default_flow_style=False)

    def get_overrides(self):
        file_name = '{}/overrides/{}.yml'.format(self.metadata['class_dir'],
                                                 self.name.replace('.', '-'))
        if 'cluster_name' not in self.metadata:
            return {}
        if not os.path.isfile(file_name):
            with open(file_name, 'w') as file_handler:
                metadata = {
                    'parameters': {
                        '_param': {
                            'cluster_name': self.metadata['cluster_name'],
                            'cluster_domain': self.metadata['cluster_domain']
                        }
                    }
                }
                file_handler.save(yaml.dump(metadata))
            return {}
        with open(file_name, 'r') as file_handler:
            metadata = yaml.load(file_handler.read())
        return metadata.get('parameters', {}).get('_param', {})

    def classify_node(self, node_name, node_data={}):
        '''
        CLassify node by current class_mapping dictionary
        '''
        inventory = Inventory.objects.get(name=self.name)
        node_data = {k: v for (k, v) in node_data.items() if not k.startswith('__pub_')}

        classes = []
        node_params = {}
        cluster_params = {}

        for type_name, node_type in inventory.cache.get('class_mapping', {}).items():
            valid = self._validate_condition(node_data, node_type.get('expression', ''))
            if valid:
                gen_classes = self._get_node_classes(node_data, node_type.get('node_class', {}))
                classes = classes + gen_classes
                gen_node_params = self._get_params(node_data, node_type.get('node_param', {}))
                node_params.update(gen_node_params)
                gen_cluster_params = self._get_params(node_data, node_type.get('cluster_param', {}))
                cluster_params.update(gen_cluster_params)

        if classes:
            node_metadata = {
                'classes': classes + ['overrides.{}'.format(self.name.replace('.', '-'))],
                'parameters': {
                    '_param': node_params,
                    'linux': {
                        'system': {
                            'name': node_name.split('.')[0],
                            'domain': '.'.join(node_name.split('.')[1:])
                        }
                    }
                }
            }
            inventory.client().resource_create(node_name, node_metadata)

        self.update_resources()

        if len(cluster_params) > 0:
            for name, value in cluster_params.items():
                self.save_override_param(name, value)

    def _get_node_classes(self, node_data, class_mapping_fragment):
        classes = []

        for value_tmpl_string in class_mapping_fragment.get('value_template', []):
            value_tmpl = Template(value_tmpl_string.replace('<<', '${')
                                                   .replace('>>', '}'))
            rendered_value = value_tmpl.safe_substitute(node_data)
            classes.append(rendered_value)

        for value in class_mapping_fragment.get('value', []):
            classes.append(value)

        return classes

    def _get_params(self, node_data, class_mapping_fragment):
        params = {}

        for param_name, param in class_mapping_fragment.items():
            value = param.get('value', None)
            value_tmpl_string = param.get('value_template', None)
            if value:
                params.update({param_name: value})
            elif value_tmpl_string:
                value_tmpl = Template(value_tmpl_string.replace('<<', '${')
                                                       .replace('>>', '}'))
                rendered_value = value_tmpl.safe_substitute(node_data)
                if value_tmpl_string.replace('<<', '${').replace('>>', '}') != rendered_value:
                    params.update({param_name: rendered_value})
        return params

    def _validate_condition(self, node_data, expressions):
        """
        Allow string expression definition for single expression conditions
        """
        if isinstance(expressions, six.string_types):
            expressions = [expressions]

        result = []
        for expression_tmpl_string in expressions:
            expression_tmpl = Template(expression_tmpl_string.replace('<<', '${')
                                                             .replace('>>', '}'))
            expression = expression_tmpl.safe_substitute(node_data)

            if expression and expression == 'all':
                result.append(True)
            elif expression:
                val_a = expression.split('__')[0]
                val_b = expression.split('__')[2]
                condition = expression.split('__')[1]
                if condition == 'startswith':
                    result.append(val_a.startswith(val_b))
                elif condition == 'equals':
                    result.append(val_a == val_b)

        return all(result)
