# -*- coding: utf-8 -*-

import requests
from architect.manager.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


DEFAULT_RESOURCES = [
    'spinnaker_account',
    'spinnaker_application',
    # 'spinnaker_artifact',
    'spinnaker_pipeline_config',
    'spinnaker_pipeline',
    # 'spinnaker_stage',
]


class SpinnakerClient(BaseClient):

    def __init__(self, **kwargs):
        super(SpinnakerClient, self).__init__(**kwargs)

    def auth(self):
        status = True
        return status

    def client(self, path):
        response = requests.get('{}{}'.format(self.metadata['auth_url'],
                                              path))
        return response.json()

    def update_resources(self, resources=None):
        if self.auth():
            if resources is None:
                resources = DEFAULT_RESOURCES
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
        metadata = []
        if kind == 'spinnaker_account':
            metadata = self.client('/credentials')
        elif kind == 'spinnaker_application':
            metadata = self.client('/applications')
        elif kind == 'spinnaker_pipeline':
            applications = self.client('/applications')
            for app in applications:
                data = self.client('/applications/{}/'
                                   'pipelines'.format(app['name']))
                if len(data) > 0:
                    metadata += data
        elif kind == 'spinnaker_pipeline_config':
            applications = self.client('/applications')
            for app in applications:
                data = self.client('/applications/{}/'
                                   'pipelineConfigs'.format(app['name']))
                if len(data) > 0:
                    metadata += data
        return metadata

    def process_resource_metadata(self, kind, metadata):
        if kind == 'spinnaker_account':
            for resource in metadata:
                self._create_resource(resource['name'],
                                      resource['name'],
                                      'spinnaker_account',
                                      metadata=resource)
        elif kind == 'spinnaker_application':
            for resource in metadata:
                self._create_resource(resource['name'],
                                      resource['name'],
                                      'spinnaker_application',
                                      metadata=resource)
        elif kind == 'spinnaker_pipeline':
            for resource in metadata:
                self._create_resource(resource['id'],
                                      resource['name'],
                                      'spinnaker_pipeline',
                                      metadata=resource)
        elif kind == 'spinnaker_pipeline_config':
            for resource in metadata:
                logger.info(resource)
                self._create_resource(resource['id'],
                                      resource['name'],
                                      'spinnaker_pipeline_config',
                                      metadata=resource)

    def process_relation_metadata(self):
        # Define relationships between pipeline configs and applications
        for resource_id, resource in self.resources.get('spinnaker_pipeline_config',
                                                        {}).items():
            self._create_relation(
                'application_pipeline_config',
                resource_id,
                resource['metadata']['application'])

        # Define relationships between pipelines and applications
        for resource_id, resource in self.resources.get('spinnaker_pipeline',
                                                        {}).items():
            self._create_relation(
                'application_pipeline',
                resource_id,
                resource['metadata']['application'])

        # Define relationships between pipelines and pipeline configurations
        for resource_id, resource in self.resources.get('spinnaker_pipeline',
                                                        {}).items():
            self._create_relation(
                'application_pipeline',
                resource_id,
                resource['metadata']['pipelineConfigId'])
