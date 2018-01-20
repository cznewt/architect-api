# -*- coding: utf-8 -*-

import json
import jenkins
import xml.etree.ElementTree as ET
from architect.manager.client import BaseClient
from six.moves.urllib.error import HTTPError
from six.moves.urllib.request import Request
from celery.utils.log import get_logger

logger = get_logger(__name__)

WF_NODE_LOG = '%(folder_url)sjob/%(short_name)s/%(number)d/execution/node/%(node)s/wfapi/log'
WF_BUILD_INFO = '%(folder_url)sjob/%(short_name)s/%(number)d/wfapi/describe'


class JenkinsExtension(object):
    """
    Stage wrapper around Jenkins client. Requires Pipeline Stage View plugin.
    """

    def get_workflows(self):
        jobs = self.client.get_jobs()
        return jobs

    def get_builds(self, name):
        job_info = self.client.get_job_info(name)
        builds = job_info['builds']

        for build in builds:
            build_info = self.client.get_build_info(name, build['number'])
            build.update(build_info)
            build['job_name'] = name
        return builds

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
        self.process_relation_metadata()

    def get_resource_status(self, kind, metadata):
        return 'unknown'

    def process_relation_metadata(self):
        pass
