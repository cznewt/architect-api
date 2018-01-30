# -*- coding: utf-8 -*-

import os
import glob
import docutils
from docutils.frontend import OptionParser
from docutils.utils import new_document
from docutils.parsers.rst import Parser
from django.conf import settings
from reclass import get_storage
from reclass.core import Core
from architect import utils
from architect.inventory.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


class SectionParserVisitor(docutils.nodes.GenericNodeVisitor):

    section_tree = []

    def visit_section(self, node):
        # Catch reference nodes for link-checking.
        print(self.section_tree)
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
        # Pass all other nodes through.
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

    def __init__(self, **kwargs):
        super(SaltFormulasClient, self).__init__(**kwargs)

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
                    'schemas': self.parse_schema_files(service)
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

    def parse_schema_files(self, formula):
        output = {}
        schemas = glob.glob('{}/*/schemas/*.yaml'.format(formula))
        for schema in schemas:
            if os.path.exists(schema):
                role_name = schema.split('/')[-1].replace('.yaml', '')
                service_name = schema.split('/')[-3]
                print(role_name, service_name)
                name = '{}-{}'.format(service_name, role_name)
                output[name] = {
                    'path': schema,
#                    'valid': schema_validate(service_name, role_name)[name]
                }
        return output
