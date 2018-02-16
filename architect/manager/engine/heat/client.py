# -*- coding: utf-8 -*-

import os
import pyaml
import glob
import tempfile
import petname
import os_client_config
from django import forms
from os_client_config import cloud_config
from heatclient.common import http
from heatclient.common import template_utils
from keystoneauth1.exceptions.connection import ConnectFailure
from urllib.error import URLError
from architect.manager.client import BaseClient
from architect.manager.models import Manager
from architect.manager.tasks import wait_for_resource_state_task
from architect.document.models import Document

from celery.utils.log import get_logger

logger = get_logger(__name__)


class HeatClient(BaseClient):

    def __init__(self, **kwargs):
        super(HeatClient, self).__init__(**kwargs)

    def auth(self):
        status = True
        manager = Manager.objects.get(name=self.metadata['cloud_endpoint'])
        if not os.path.isdir(self.metadata['template_path']):
            status = False
        try:
            config_file, filename = tempfile.mkstemp()
            config_content = {
                'clouds': {self.name: manager.metadata}
            }
            os.write(config_file, pyaml.dump(config_content).encode())
            os.close(config_file)
            self.cloud = os_client_config.config \
                .OpenStackConfig(config_files=[filename]) \
                .get_one_cloud(cloud=self.name)
            os.remove(filename)
            self.api = self._get_client('orchestration')
        except ConnectFailure as exception:
            logger.error(exception)
            status = False
        return status

    def _get_client(self, service_key):
        constructor = cloud_config._get_client(service_key)
        return self.cloud.get_legacy_client(service_key, constructor)

    def update_resources(self, resources=None):
        if self.auth():
            if resources is None:
                resources = [
                    'heat_template',
                    'heat_stack',
                    # 'heat_resource',
                ]
            for resource in resources:
                metadata = self.get_resource_metadata(resource)
                self.process_resource_metadata(resource, metadata)
                count = len(self.resources.get(resource, {}))
                logger.info("Processed {} {} resources".format(count,
                                                               resource))
            self.process_relation_metadata()

    def get_resource_status(self, kind, metadata):
        if not isinstance(metadata, dict):
            return 'unknown'
        if kind == 'heat_stack':
            stack_status = metadata.get('stack_status', '')
            if stack_status in ['CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
                return 'build'
            elif stack_status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                return 'active'
            elif stack_status in ['CREATE_FAILED', 'UPDATE_FAILED', 'DELETE_FAILED']:
                return 'error'
        return 'unknown'

    def get_resource_metadata(self, kind, uid=None):
        logger.info("Getting {} resources".format(kind))
        response = {}
        if kind == 'heat_template':
            path = self.metadata['template_path']
            if uid is None:
                templates = glob.glob('{}/*.hot'.format(path))
                for template in templates:
                    with open(template) as file_handler:
                        data = file_handler.read()
                    response[template.replace('{}/'.format(path), '')] = data
            else:
                template = '{}/{}'.format(path, uid)
                with open(template) as file_handler:
                    data = file_handler.read()
                    response[uid] = data
        elif kind == 'heat_stack':
            if uid is None:
                stacks = self.api.stacks.list()
                for stack in stacks:
                    resource = stack.to_dict()
                    response[resource['id']] = resource
            else:
                stack = self.api.stacks.get(uid)
                resource = stack.to_dict()
                response[resource['id']] = resource
        elif kind == 'heat_resource':
            stacks = self.orch_api.stacks.list()
            for stack in stacks:
                resource = stack.to_dict()
                resource['resources'] = {}
                try:
                    resources = self.api.resources.list(resource['id'],
                                                        nested_depth=2)
                    for stack_resource in resources:
                        res_dict = stack_resource.to_dict()
                        stack_id = None
                        nested_stack_id = None
                        for link in res_dict['links']:
                            if link['rel'] == 'stack':
                                stack_id = link['href'].split('/')[-2]
                            if link['rel'] == 'nested':
                                nested_stack_id = link['href'].split('/')[-2]
                        if nested_stack_id is None:
                            res_stack = stack_id
                        else:
                            res_stack = nested_stack_id
                        if res_stack not in resource['resources']:
                            resource['resources'][res_stack] = {'res': {}, 'stack': resource}
                        resource['resources'][res_stack]['res'][res_dict['resource_name']] = res_dict
                except HTTPBadRequest as exception:
                    logger.error(exception)
                response[resource['id']] = resource
        return response

    def process_resource_metadata(self, kind, metadata):
        if kind == 'heat_template':
            for resource_name, resource in metadata.items():
                self._create_resource(resource_name,
                                      resource_name,
                                      'heat_template',
                                      metadata=resource)
        elif kind == 'heat_stack':
            for resource_name, resource in metadata.items():
                self._create_resource(resource_name,
                                      resource['stack_name'],
                                      'heat_stack',
                                      metadata=resource)

    def process_relation_metadata(self):
        pass

    def generate_name(self, separator='-', word_count=2):
        return petname.Generate(int(word_count), separator)

    def create_resource(self, kind, metadata):
        logger.info("Creating {} resource".format(kind))

        if kind == 'heat_stack':
            if self.auth():
                tpl_files, template = template_utils.get_template_contents(
                    template_file=metadata['template_file'],
                    object_request=http.authenticated_fetcher(self.api))
                env_files_list = []
                env_files, env = template_utils.process_multiple_environments_and_files(
                    env_paths=[metadata['environment_file']],
                    env_list_tracker=env_files_list)
                fields = {
                    'stack_name': metadata['name'],
                    'disable_rollback': True,
                    'parameters': metadata['parameters'],
                    'template': template,
                    'files': dict(list(tpl_files.items()) + list(env_files.items())),
                    'environment': env
                }
                if env_files_list:
                    fields['environment_files'] = env_files_list
                response = self.api.stacks.create(**fields)
                logger.info(response)
                stack = self.api.stacks.get(response['stack']['id'])
                resource = stack.to_dict()
                stack_metadata = {resource['id']: resource}
                template_metadata = self.get_resource_metadata('heat_template',
                                                               metadata['template_name'])
                self.process_resource_metadata('heat_template', template_metadata)
                self.process_resource_metadata('heat_stack', stack_metadata)
                self._create_relation(
                    'defined_by',
                    resource['id'],
                    metadata['template_name'])
                self.save()
                document_name = '{}.{}'.format(
                    resource['parameters']['OS::stack_name'],
                    resource['parameters']['cluster_domain']
                )
                widget_name = '01-heat-stack-resources'
                widget_meta = {
                    'name': 'Heat resources',
                    'update_interval': 9,
                    'width': 'col-sm-6 col-md-6 mb-3',
                    'height': 1,
                    'chart': 'tree',
                    'data_source': {
                        'default': {
                            'type': 'relational',
                            'source': self.name,
                            'query': 'heat_template_stacks_tree',
                        }
                    }
                }
                document, created = Document.objects.get_or_create(name=document_name)
                if created:
                    document.metadata = {'widget': {}}
                    document.save()
                document.add_widget(widget_name, widget_meta)
                document.save()
                logger.info(stack)
                wait_for_resource_state_task.apply_async((self.name,
                                                          resource['id'],
                                                          ['active', 'error']))

    def get_resource_action_fields(self, resource, action):
        fields = {}
        if resource.kind == 'heat_template':
            if action == 'create':
                initial_name = '{}-{}'.format(resource.name.replace('.hot', '').replace('_', '-'),
                                              self.generate_name())
                fields['name'] = forms.CharField(label='Stack name',
                                                 initial=initial_name)
                fields['environment'] = forms.ChoiceField(label='Environment',
                                                        choices=self.get_environment_choices())
        return fields

    def process_resource_action(self, resource, action, data):
        if resource.kind == 'heat_template':
            if action == 'create':
                metadata = {
                    'name': data['name'],
                    'template_file': '{}/{}'.format(self.metadata['template_path'],
                                                    resource.name),
                    'environment_file': data['environment'],
                    'parameters': [],
                    'template_name': resource.name
                }
                try:
                    self.create_resource('heat_stack', metadata)
                except URLError as exception:
                    logger.error(exception)

    def get_environment_choices(self):
        choices = []
        if self.metadata.get('context_source', 'local') == 'local':
            path = self.metadata['context_path']
            contexts = glob.glob('{}/*'.format(path))
            for context in contexts:
                choices.append((context,
                                context.replace('{}/'.format(path), '')))
        return choices
