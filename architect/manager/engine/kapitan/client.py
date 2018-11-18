# -*- coding: utf-8 -*-

import os
import re
import six
import subprocess
import yaml
import json
import petname
import boto3
from kapitan.targets import compile_targets
from kapitan.refs.base import RefController, Revealer
from django import forms
from django.conf import settings
from urllib.error import URLError
from architect.manager.client import BaseClient
from architect.manager.models import Manager
from celery.utils.log import get_logger

logger = get_logger(__name__)


DEFAULT_RESOURCES = [
    'kapitan_target',
]


class KapitanClientError(Exception):
    pass


class KapitanClient(BaseClient):

    def __init__(self, **kwargs):
        super(KapitanClient, self).__init__(**kwargs)

    def auth(self):
        if os.path.isdir(self.metadata['base_dir']):
            return True
        else:
            return False

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

    def get_resource_metadata(self, kind, uid=None):
        logger.info("Getting {} resources".format(kind))
        response = {}
        if kind == 'kapitan_target':
            inventory_dir = self.metadata['inventory_dir']
            output_dir = self.metadata['base_dir']
            vendor_dir = self.metadata['base_dir'] + '/vendor'
            parallelism = '8'
            cmd = [
                'kapitan',
                'compile',
                '--inventory-path',
                inventory_dir,
                '--output-path',
                output_dir,
                '--search-paths',
                self.metadata['base_dir'],
                vendor_dir,
                '--parallelism',
                parallelism
            ]
            output = self._cmd_run(cmd)
            logger.info(output)
            config = settings.ARCHITECT_STORAGE[self.metadata['publish_storage']]
            client = boto3.client('s3',
                                  aws_access_key_id=config['access_key'],
                                  aws_secret_access_key=config['secret_key'],
                                  endpoint_url='http://' + config['endpoint'],
                                  config=boto3.session.Config(signature_version='s3v4')
                                  )
            for root, dirs, files in os.walk(self.metadata['base_dir'] + '/compiled'):
                for filename in files:
                    local_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(local_path, self.metadata['base_dir'] + '/compiled')
                    try:
                        client.head_object(Bucket=config['bucket'], Key=relative_path)
                        try:
                            client.delete_object(Bucket=config['bucket'], Key=relative_path)
                        except:
                            pass
                    except:
                        pass
                    client.upload_file(local_path, config['bucket'], relative_path)
        return response

    def get_resource_status(self, kind, metadata):
        if kind == 'kapitan_target':
            return 'active'
        return 'unknown'

    def process_resource_metadata(self, kind, metadata):
        if kind == 'kapitan_target':
            for resource_name, resource in metadata.items():
                self._create_resource(resource_name.split('/')[-1],
                                      resource_name,
                                      'kapitan_target',
                                      metadata=resource)

    def process_relation_metadata(self):
        for resource_id, resource in self.resources.get('kapitan_target',
                                                        {}).items():
            self._create_relation(
                'defined_by',
                resource_id,
                '-'.join(resource['metadata']['chart'].split('-')[:-1]))

    def generate_name(self, separator='-', word_count=2):
        return petname.Generate(int(word_count), separator)

    def get_resource_action_fields(self, resource, action):
        fields = {}
        if resource.kind == 'kapitan_target':
            if action == 'create':
                initial_name = '{}-{}'.format(resource.name.replace('/', '-'),
                                              self.generate_name())
                fields['name'] = forms.CharField(label='Release name',
                                                 initial=initial_name)
        return fields

    def process_resource_action(self, resource, action, data):
        if resource.kind == 'kapitan_target':
            if action == 'create':
                pass

    def _cmd_run(self, cmd):
        if isinstance(cmd, six.string_types):
            cmd = cmd.split()
        res = subprocess.run(cmd,
                             env=os.environ.copy(),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        if res.returncode != 0:
            raise KapitanClientError(res.stderr.decode('utf-8'))
        return res.stdout.decode('utf-8')
