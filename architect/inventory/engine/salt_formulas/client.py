# -*- coding: utf-8 -*-

import os
import re
import yaml
import glob
import docutils
from collections import OrderedDict
from docutils.frontend import OptionParser
from docutils.utils import new_document
from docutils.parsers.rst import Parser
from django.conf import settings
from reclass import get_storage
from reclass.core import Core
from architect import utils
from architect.inventory.client import BaseClient
from celery.utils.log import get_logger
from jsonschema import validate
from jsonschema.validators import validator_for
from jsonschema.exceptions import SchemaError, ValidationError

logger = get_logger(__name__)


class SectionParserVisitor(docutils.nodes.GenericNodeVisitor):

    section_tree = []

    def visit_section(self, node):
        if node.parent is None:
            parent = 'document-root'
        else:
            parents = node.parent['ids']
            if len(parents) > 0:
                parent = parents[0]
            else:
                parent = 'document-root'
        self.section_tree.append((node['ids'][0], parent,))

    def default_visit(self, node):
        pass

    def reset_section_tree(self):
        self.section_tree = []

    def get_section_tree(self):
        return self.sub_tree('document-root', self.section_tree)

    def sub_tree(self, node, relationships):
        return {
            v: self.sub_tree(v, relationships)
            for v in [x[0] for x in relationships if x[1] == node]
        }


class SaltFormulasClient(BaseClient):

    class_cache = {}

    def __init__(self, **kwargs):
        super(SaltFormulasClient, self).__init__(**kwargs)

    def check_status(self):
        try:
            data = self.inventory()
            status = True
        except Exception:
            status = False
        return status

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

    def get_base_dir(self):
        return self.metadata['formula_dir']

    def dict_deep_merge(self, a, b, path=None):
        """
        Merges dict(b) into dict(a)
        """
        if path is None:
            path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    self.dict_deep_merge(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass  # same leaf value
                else:
                    raise Exception(
                        'Conflict at {}'.format('.'.join(path + [str(key)])))
            else:
                a[key] = b[key]
        return a

    def formula_class_list(self):
        return []

    def formula_list(self):
        output = {}
        services = glob.glob('{}/*'.format(self.get_base_dir()))
        for service in services:
            if os.path.exists(service):
                service_name = service.split('/')[-1]
                output[service_name] = {
                    'path': service,
                    'metadata': self.parse_metadata_file(service),
                    'readme': self.parse_readme_file(service),
                    'schemas': self.parse_schema_files(service),
                    'support_files': self.parse_support_files(service)
                }
        return output

    def parse_metadata_file(self, formula):
        metadata_file = '/{}/metadata.yml'.format(formula)
        return utils.load_yaml_json_file(metadata_file)

    def parse_readme_file(self, formula):
        settings = OptionParser(components=(Parser,)).get_default_values()
        parser = Parser()
        input_file = open('{}/README.rst'.format(formula))
        input_data = input_file.read()
        document = new_document(input_file.name, settings)
        parser.parse(input_data, document)
        visitor = SectionParserVisitor(document)
        visitor.reset_section_tree()
        document.walk(visitor)
        input_file.close()
        return visitor.get_section_tree()

    def parse_support_files(self, formula):
        output = []
        support_files = glob.glob('{}/*/meta/*.yml'.format(formula))
        for support_file in support_files:
            if os.path.exists(support_file):
                service_name = support_file.split('/')[-1].replace('.yml', '')
                output.append(service_name)
        return output

    def parse_schema_files(self, formula):
        output = {}
        schemas = glob.glob('{}/*/schemas/*.yaml'.format(formula))
        for schema in schemas:
            if os.path.exists(schema):
                role_name = schema.split('/')[-1].replace('.yaml', '')
                service_name = schema.split('/')[-3]
                name = '{}-{}'.format(service_name, role_name)
                output[name] = {
                    'path': schema,
#                    'valid': schema_validate(service_name, role_name)[name]
                }
        return output

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
        if len(self.class_cache) > 0:
            return self.class_cache
        data = self.walk_raw_classes(ret_classes=True)
        return_data = {}
        for name, datum in data.items():
            name = name[1:]
            if prefix is None:
                return_data[name] = datum
            elif name.startswith(prefix):
                return_data[name] = datum
        self.class_cache = OrderedDict(sorted(return_data.items(),
                                              key=lambda t: t[0]))
        return self.class_cache

    def service_class_list(self):
        return self.raw_class_list('service.')

    def system_class_list(self):
        return self.raw_class_list('system.')

    def cluster_class_list(self):
        return self.raw_class_list('cluster.')

    def raw_class_get(self, name):
        '''
        Returns detailes information about class file in reclass inventory.
        '''
        classes = self.raw_class_list()
        return {name: classes.get(name)}
