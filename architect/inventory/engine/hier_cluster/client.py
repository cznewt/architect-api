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
from architect import utils
from architect.inventory.client import BaseClient
from architect.inventory.models import Resource, Inventory
from celery.utils.log import get_logger

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


class HierClusterClient(BaseClient):

    class_cache = {}

    def __init__(self, **kwargs):
        super(HierClusterClient, self).__init__(**kwargs)

    def check_status(self):
        logger.info(self.metadata)
        status = True
        if not os.path.exists(self.metadata['formula_dir']):
            status = False
        if not os.path.exists(self.metadata['class_dir']):
            status = False
        return status

    def update_resources(self):
        inventory = Inventory.objects.get(name=self.name)
        service_formulas = self.list_formulas()
        for formula_name, formula in service_formulas.items():
            res, created = Resource.objects.get_or_create(
                uid=formula_name,
                kind='service_formula',
                inventory=inventory)
            if created:
                res.metadata = formula
                res.save()
            else:
                if res.metadata != formula:
                    res.metadata = formula
                    res.save()

        logger.info('Processed {} service'
                    ' formulas'.format(len(service_formulas)))
        classes = self.list_classes()
        for class_name, class_meta in classes.items():
            cluster_classes = {}
            system_classes = {}
            service_classes = {}
            if '.' not in class_name:
                continue
            top_name = class_name.split('.')[1]
            if class_name.startswith('service.'):
                if top_name not in service_classes:
                    service_classes[top_name] = {}
                service_classes[top_name][class_name] = class_meta
                res, created = Resource.objects.get_or_create(
                    uid=class_name,
                    name=class_name,
                    kind='service_class',
                    inventory=inventory)
                if created:
                    res.metadata = class_meta
                else:
                    if res.metadata != class_meta:
                        res.metadata = class_meta
                res.save()

            elif class_name.startswith('system.'):
                if top_name not in system_classes:
                    system_classes[top_name] = {}
                system_classes[top_name][class_name] = class_meta
                res, created = Resource.objects.get_or_create(
                    uid=class_name,
                    name=class_name,
                    kind='system_class',
                    inventory=inventory)
                if created:
                    res.metadata = class_meta
                else:
                    if res.metadata != class_meta:
                        res.metadata = class_meta
                res.save()

            elif class_name.startswith('cluster.'):
                if top_name not in cluster_classes:
                    cluster_classes[top_name] = {}
                cluster_classes[top_name][class_name] = class_meta
                res, created = Resource.objects.get_or_create(
                    uid=class_name,
                    name=class_name,
                    kind='cluster_class',
                    inventory=inventory)
                if created:
                    res.metadata = class_meta
                else:
                    if res.metadata != class_meta:
                        res.metadata = class_meta
                res.save()

            for unit, unit_classes in cluster_classes.items():
                res, created = Resource.objects.get_or_create(
                    uid=unit,
                    name=unit,
                    kind='cluster_unit',
                    inventory=inventory)
                if created:
                    res.metadata = unit_classes
                else:
                    if res.metadata != unit_classes:
                        res.metadata = unit_classes
                res.save()

            for unit, unit_classes in system_classes.items():
                res, created = Resource.objects.get_or_create(
                    uid=unit,
                    name=unit,
                    kind='system_unit',
                    inventory=inventory)
                if created:
                    res.metadata = unit_classes
                else:
                    if res.metadata != unit_classes:
                        res.metadata = unit_classes
                res.save()

        logger.info('Processed {} classes'.format(len(classes)))

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

    def list_formulas(self):
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
                    'support_files': self.parse_support_files(service),
                }
        return output

    def parse_metadata_file(self, formula):
        metadata_file = '/{}/metadata.yml'.format(formula)
        return utils.load_yaml_json_file(metadata_file)

    def parse_readme_file(self, formula):
        settings = OptionParser(
            components=(Parser,)).get_default_values()
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
                    # 'valid': schema_validate(service_name, role_name)[name]
                }
        return output

    def walk_classes(self, ret_classes=True, ret_errors=False):
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
                class_name = class_file.replace(
                    path, '')[:-9].replace('/', '.')
                classes[class_name] = {'file': class_file}

            for f in files:
                if f.endswith('.yml') and f != 'init.yml':
                    class_file = root + '/' + f
                    class_name = class_file.replace(
                        path, '')[:-4].replace('/', '.')
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
                    if data.get('parameters') and \
                       data['parameters'].get('_param'):
                        params['params_created'] = data['parameters']['_param']

                    if not(data.get('classes') or data.get('parameters')):
                        errors.append('{} file missing classes and '
                                      'parameters'.format(params['file']))
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

    def list_classes(self, prefix=None):
        '''
        Returns list of all classes defined in reclass inventory. You can
        filter returned classes by prefix.
        '''
        if len(self.class_cache) > 0:
            return self.class_cache
        data = self.walk_classes(ret_classes=True)
        return_data = {}
        for name, datum in data.items():
            name = name[1:]
            if prefix is None:
                return_data[name] = datum
            elif name.startswith(prefix):
                return_data[name] = datum
        if len(self.class_cache) == 0:
            self.class_cache = OrderedDict(sorted(return_data.items(),
                                                  key=lambda t: t[0]))
        return self.class_cache

    def list_service_classes(self):
        return self.list_classes('service.')

    def list_system_classes(self):
        return self.list_classes('system.')

    def list_cluster_classes(self):
        return self.list_classes('cluster.')

    def get_class(self, name):
        '''
        Returns detailes information about class file in reclass inventory.
        '''
        classes = self.list_classes()
        return {
            name: classes.get(name)
        }
