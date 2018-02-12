# -*- coding: utf-8 -*-

import os
import re
import six
import subprocess
import yaml
import json
import petname
import tempfile
from django import forms
from urllib.error import URLError
from architect.manager.client import BaseClient
from architect.manager.models import Manager
from celery.utils.log import get_logger

logger = get_logger(__name__)


class HelmClientError(Exception):
    pass


class HelmClient(BaseClient):

    def __init__(self, **kwargs):
        super(HelmClient, self).__init__(**kwargs)

    def auth(self):
        status = True
        manager = Manager.objects.get(name=self.metadata['container_endpoint'])
        try:
            config_file, filename = tempfile.mkstemp()
            config_content = {
                'apiVersion': 'v1',
                'clusters': [{
                    'cluster': manager.metadata['cluster'],
                    'name': self.name,
                }],
                'contexts': [{
                    'context': {
                        'cluster': self.name,
                        'user': self.name,
                    },
                    'name': self.name,
                }],
                'current-context': self.name,
                'kind': 'Config',
                'preferences': {},
                'users': [{
                    'name': self.name,
                    'user': manager.metadata['user']
                }]
            }
            self.kubeconfig = config_content
            config_file = open(self.get_config_filename(), "w+")
            config_file.write(json.dumps(config_content))
            config_file.close()
        except URLError as exception:
            logger.error(exception)
            status = False

        try:
            self.version()
        except HelmClientError as exception:
            logger.error(exception)
            status = False

        return status

    def update_resources(self, resources=None):
        if self.auth():
            if resources is None:
                resources = [
                    'helm_chart',
                    'helm_release',
                ]
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
        if kind == 'helm_chart':
            charts = self.search()
            chart_names = [c['name'] for c in charts]
            for chart_name in chart_names:
                metadata = self.inspect(chart_name)
                response[chart_name] = metadata
            return response
        if kind == 'helm_release':
            response = self.list()
        return response

    def get_resource_status(self, kind, metadata):
        if kind == 'helm_chart':
            return 'active'
        elif kind == 'helm_release':
            if metadata['status'] == 'DEPLOYED':
                return 'active'
        return 'unknown'

    def process_resource_metadata(self, kind, metadata):
        if kind == 'helm_chart':
            for resource_name, resource in metadata.items():
                self._create_resource(resource_name.split('/')[-1],
                                      resource_name,
                                      'helm_chart',
                                      metadata=resource)
        elif kind == 'helm_release':
            for resource in metadata:
                self._create_resource(resource['name'],
                                      resource['name'],
                                      'helm_release',
                                      metadata=resource)

    def process_relation_metadata(self):
        for resource_id, resource in self.resources.get('helm_release',
                                                        {}).items():
            self._create_relation(
                'defined_by',
                resource_id,
                '-'.join(resource['metadata']['chart'].split('-')[:-1]))

    def get_config_filename(self):
        return '{}/kubeconfig'.format(self.metadata['chart_path'])

    def _cmd_run(self, cmd):
        if isinstance(cmd, six.string_types):
            cmd = cmd.split()
        env = os.environ.copy()
        env['KUBECONFIG'] = self.get_config_filename()
        final_cmd = [self.metadata['helm_bin']] + cmd + \
                    ['--home', self.metadata['chart_path']]
        res = subprocess.run(final_cmd,
                             env=env,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        if res.returncode != 0:
            raise HelmClientError(res.stderr.decode('utf-8'))
        return res.stdout.decode('utf-8')

    def _parse_noop(self, response):
        return {'raw': response}

    def _parse_horizontal(self, response, keys):
        parsed = []
        lines = response.splitlines()
        if lines:
            del lines[0]
            for line in lines:
                parsed_line = re.split(r'\t+', line)
                clean_line = [ch.rstrip() for ch in parsed_line]
                item = dict(zip(keys, clean_line))
                parsed.append(item)
        return parsed

    def _parse_inspect(self, raw_data):
        _chart = raw_data.split('\n---')[0]
        _values = raw_data.split('\n---')[1]
        try:
            chart = yaml.load(_chart)
        except Exception:
            chart = {}
        try:
            values = yaml.load(_values)
        except Exception:
            values = {}
        return {
            'chart': chart,
            'values': values
        }

    def _parse_list(self, response):
        keys = ['name', 'revision', 'updated', 'status', 'chart', 'namespace']
        return self._parse_horizontal(response, keys)

    def list(self):
        raw = self._cmd_run('list')
        return self._parse_list(raw)

    def search(self, chart=None):
        cmd = 'search'
        if chart:
            cmd = cmd + ' {}'.format(chart)
        raw_data = self._cmd_run(cmd)
        keys = ['name', 'version', 'description']
        return self._parse_horizontal(raw_data, keys)

    def version(self):
        raw_data = self._cmd_run('version')
        return self._parse_noop(raw_data)

    def init(self):
        raw_data = self._cmd_run('init')
        return self._parse_noop(raw_data)

    def inspect(self, chart):
        raw_data = self._cmd_run('inspect {}'.format(chart))
        return self._parse_inspect(raw_data)

    def install(self, chart, release_name=None, overrides=None):
        cmd = 'install'
        if release_name:
            cmd = cmd + ' --name={}'.format(release_name)
        if overrides and isinstance(overrides, dict):
            ovrdhandle, ovrdpath = tempfile.mkstemp(prefix='khelm-ovrd-')
            with open(ovrdpath, 'w') as outfile:
                json.dump(overrides, outfile)
            cmd = cmd + ' -f {}'.format(ovrdpath)
        cmd = cmd + ' {}'.format(chart)
        raw_data = self._cmd_run(cmd)
        try:
            os.close(ovrdhandle)
            os.remove(ovrdpath)
        except Exception:
            pass
        return self._parse_noop(raw_data)

    def generate_name(self, separator='-', word_count=2):
        return petname.Generate(int(word_count), separator)

    def get_resource_action_fields(self, resource, action):
        fields = {}
        if resource.kind == 'helm_chart':
            if action == 'create':
                initial_name = '{}-{}'.format(resource.name.replace('/', '-'),
                                              self.generate_name())
                fields['name'] = forms.CharField(label='Release name',
                                                 initial=initial_name)
        return fields

    def process_resource_action(self, resource, action, data):
        if resource.kind == 'helm_chart':
            if action == 'create':
                self.install(resource.name, data['name'])
