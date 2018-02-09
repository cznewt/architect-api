# -*- coding: utf-8 -*-

import os
import re
import six
import subprocess
import json
import tempfile
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
        self.process_relation_metadata()

    def get_resource_status(self, kind, metadata):
        return 'unknown'

    def process_relation_metadata(self):
        logger.info(self.version())
        pass

    def get_config_filename(self):
        return '{}/kubeconfig'.format(self.metadata['chart_path'])

    def _cmd_run(self, cmd):
        if isinstance(cmd, six.string_types):
            cmd = cmd.split()
        env = os.environ.copy()
        env['KUBECONFIG'] = self.get_config_filename()
        final_cmd = [self.metadata['helm_bin']] + cmd
        logger.error(final_cmd)
        logger.error(env)
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

    def search(self, chart=None):
        cmd = 'search'
        if chart:
            cmd = cmd + ' {}'.format(chart)
        raw_data = self._cmd_run(cmd)
        keys = ['name', 'version', 'description']
        return self._parse_horizontal(raw_data, keys)

    def version(self):
        raw = self._cmd_run('version')
        return self._parse_noop(raw)
