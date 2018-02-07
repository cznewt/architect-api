# -*- coding: utf-8 -*-

import os
import pyaml
import glob
import tempfile
import os_client_config
from os_client_config import cloud_config
from heatclient.common import http
from heatclient.common import template_format
from heatclient.common import template_utils
from heatclient.common import utils
from keystoneauth1.exceptions.connection import ConnectFailure
from architect.manager.client import BaseClient
from architect.manager.models import Manager
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
            logger.info(self.api.__class__)
            logger.info(dir(self.api))
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
                ]
            for resource in resources:
                metadata = self.get_resource_metadata(resource)
                self.process_resource_metadata(resource, metadata)
                count = len(self.resources.get(resource, {}))
                logger.info("Processed {} {} resources".format(count,
                                                               resource))
            self.process_relation_metadata()

    def get_resource_status(self, kind, metadata):
        return 'unknown'

    def get_resource_metadata(self, kind):
        logger.info("Getting {} resources".format(kind))
        response = {}
        if kind == 'heat_template':
            path = self.metadata['template_path']
            templates = glob.glob('{}/*.hot'.format(path))
            for template in templates:
                with open(template) as file_handler:
                    data = file_handler.read()
                response[template.replace('{}/'.format(path), '')] = data
        return response

    def process_resource_metadata(self, kind, metadata):
        if kind == 'heat_template':
            for resource_name, resource in metadata.items():
                self._create_resource(resource_name,
                                      resource_name,
                                      'heat_template',
                                      metadata=resource)

    def create_resource(self, kind, metadata):
        logger.info("Creating {} resource".format(kind))

        if kind == 'heat_stack':
            if self.auth():
                tpl_files, template = template_utils.get_template_contents(
                    template_file=metadata['template_file'],
                    object_request=http.authenticated_fetcher(self.api))
                env_files_list = []
                logger.info(metadata)
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
                logger.info(fields)
                if env_files_list:
                    fields['environment_files'] = env_files_list
                self.api.stacks.create(**fields)

    def process_relation_metadata(self):
        pass
