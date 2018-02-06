# -*- coding: utf-8 -*-

import json
import pyaml
import jenkins
import xml.etree.ElementTree as ET
from architect.manager.client import BaseClient
from six.moves.urllib.error import HTTPError
from six.moves.urllib.request import Request
from celery.utils.log import get_logger

logger = get_logger(__name__)

WF_NODE_LOG = '%(folder_url)sjob/%(short_name)s/%(number)d/execution/node/%(node)s/wfapi/log'
WF_BUILD_INFO = '%(folder_url)sjob/%(short_name)s/%(number)d/wfapi/describe'

DEFAULT_RESOURCES = [
    'jenkins_pipeline',
    'jenkins_build',
#    'jenkins_stage',
]


class JenkinsExtension(object):
    """
    Stage wrapper around Jenkins client. Requires Pipeline Stage View plugin.
    """

    def get_workflows(self):
        jobs = self.client.get_jobs()
        return jobs

    def get_builds(self, name):
        job_info = self.client.get_job_info(name, depth=1)
        return job_info

    def get_tree(self):
        works = self.get_workflows()
        for work in works:
            myConfig = self._client.get_job_config(work['name'])
            tree = ET.ElementTree(ET.fromstring(myConfig))
            root = tree.getroot()
            result = []
            for child in root:
                result += child.attrib
        return result

    def get_wf_build_info(self, name, number):
        """
        Get build information dictionary.

        :param name: Job name, ``str``
        :param name: Build number, ``int``
        :returns: dictionary of build information, ``dict``
        """
        folder_url, short_name = self.client._get_job_folder(name)
        try:
            response = self.client.jenkins_open(Request(
                self._build_url(WF_BUILD_INFO, locals())
            ))
            if response:
                return json.loads(response)
            else:
                raise jenkins.JenkinsException('job[%s] number[%d] does not exist'
                                               % (name, number))
        except HTTPError:
            raise jenkins.JenkinsException('job[%s] number[%d] does not exist'
                                           % (name, number))
        except ValueError:
            raise jenkins.JenkinsException(
                'Could not parse JSON info for job[%s] number[%d]'
                % (name, number)
            )

    def get_wf_node_log(self, name, number, node):
        """
        Get build log for execution node.

        :param name: Job name, ``str``
        :param name: Build number, ``int``
        :param name: Execution node number, ``int``
        :returns: Execution node build log,  ``dict``
        """
        folder_url, short_name = self.client._get_job_folder(name)
        try:
            response = self.client.jenkins_open(Request(
                self.client._build_url(WF_NODE_LOG, locals())
            ))
            if response:
                return json.loads(response)
            else:
                raise jenkins.JenkinsException('job[%s] number[%d] does not exist'
                                               % (name, number))
        except HTTPError:
            raise jenkins.JenkinsException('job[%s] number[%d] does not exist'
                                           % (name, number))


class JenkinsClient(BaseClient):

    def __init__(self, **kwargs):
        super(JenkinsClient, self).__init__(**kwargs)

    def auth(self):
        status = True
        try:
            _client = jenkins.Jenkins(self.metadata['auth_url'],
                                      username=self.metadata['username'],
                                      password=self.metadata['password'])
            extension = JenkinsExtension()
            extension.client = _client
            for method in [method for method in dir(extension)
                           if callable(getattr(extension, method)) and not method.startswith("__")]:
                setattr(_client, method, getattr(extension, method))
            self.api = _client

        except HTTPError as exception:
            logger.error(exception)
            status = False
        return status

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
        if kind == 'jenkins_pipeline':
            if metadata['color'] == 'blue':
                return 'active'
            elif metadata['color'] == 'red':
                return 'error'
        return 'unknown'

    def process_resource_metadata(self, kind, metadata):
        if kind == 'jenkins_pipeline':
            for resource in metadata:
                self._create_resource(resource['name'],
                                      resource['fullname'],
                                      'jenkins_pipeline',
                                      metadata=resource)
        elif kind == 'jenkins_build':
            for resource in metadata:
                self._create_resource('{}|{}'.format(resource['job_name'],
                                                     resource['id']),
                                      resource['fullDisplayName'],
                                      'jenkins_build',
                                      metadata=resource)

    def get_resource_metadata(self, kind):
        logger.info("Getting {} resources".format(kind))
        if kind == 'jenkins_pipeline':
            response = self.api.get_workflows()
        elif kind == 'jenkins_build':
            logger.info(self.metadata.get('pipelines', []))
            for pipeline in self.metadata.get('pipelines', []):
                data = self.api.get_builds(pipeline).get('builds', [])
                response = []
                for datum in data:
                    datum['job_name'] = pipeline
                    response.append(datum)
        return response

    def process_relation_metadata(self):
        for resource_id, resource in self.resources.get('jenkins_build',
                                                        {}).items():
            self._create_relation(
                'pipeline_run',
                resource_id,
                resource['metadata']['job_name'])
