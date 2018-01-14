# -*- coding: utf-8 -*-

from django.conf import settings
from urllib.error import URLError
from pepper.libpepper import Pepper, PepperException
from architect.manager.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


class SaltStackClient(BaseClient):

    def __init__(self, **kwargs):
        super(SaltStackClient, self).__init__(**kwargs)

    def auth(self):
        status = True
        try:
            self.api = Pepper(self.metadata['auth_url'])
            self.api.login(self.metadata['username'],
                           self.metadata['password'],
                           'pam')
        except PepperException as exception:
            logger.error(exception)
            status = False
        except URLError as exception:
            logger.error(exception)
            status = False
        return status

    def update_resources(self, resources=None):
        if self.auth():
            if resources is None:
                resources = [
                    'salt_minion',
                    'salt_service',
                    'salt_lowstate',
                    # 'salt_job',
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
        if kind == 'salt_minion':
            if 'id' in metadata:
                return 'active'
        return 'unknown'

    def get_resource_metadata(self, kind):
        logger.info("Getting {} resources".format(kind))
        if kind == 'salt_job':
            metadata = self.api.low([{
                'client': 'runner',
                'fun': 'jobs.list_jobs',
                'arg': "search_function='[\"state.apply\", \"state.sls\"]'"
            }]).get('return')[0]
        elif kind == 'salt_lowstate':
            metadata = self.api.low([{
                'client': 'local',
                'tgt': '*',
                'fun': 'state.show_lowstate'
            }]).get('return')[0]
        elif kind == 'salt_minion':
            metadata = self.api.low([{
                'client': 'local',
                'tgt': '*',
                'fun': 'grains.items'
            }]).get('return')[0]
        elif kind == 'salt_service':
            metadata = self.api.low([{
                'client': 'local',
                'tgt': '*',
                'fun': 'pillar.data'
            }]).get('return')[0]
        else:
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}
        return metadata

    def process_resource_metadata(self, kind, metadata):
        if kind == 'salt_event':
            for datum_name, datum in metadata.items():
                uid = '{}|{}'.format(data['id'], datum['__id__'])
                lowstate = SaltLowstateNode.nodes.get_or_none(uid=uid)
                to_save = False
                if lowstate is not None:
                    if 'apply' not in lowstate.metadata:
                        lowstate.metadata['apply'] = []
                        lowstate.metadata['apply'].append(datum)
                        if datum['result']:
                            lowstate.status = 'Active'
                        else:
                            lowstate.status = 'Error'
                        to_save = True
                    else:
                        if lowstate.metadata['apply'][-1]['result'] != datum['result']:
                            lowstate.metadata['apply'].append(datum)
                            if datum['result']:
                                lowstate.status = 'Active'
                            else:
                                lowstate.status = 'Error'
                            to_save = True
                if to_save:
                    lowstate.save()
        elif kind == 'salt_job':
            for job_id, job in metadata.items():
                if not isinstance(job, dict):
                    continue
                if job['Function'] in ['state.apply', 'state.sls']:
                    result = self.api.lookup_jid(job_id).get('return')[0]
                    job['Result'] = result
                    self._create_resource(job_id,
                                          job['Function'],
                                          'salt_job',
                                          metadata=job)
                    self._create_resource(job['User'],
                                          job['User'].replace('sudo_', ''),
                                          'salt_user',
                                          metadata={})
        elif kind == 'salt_lowstate':
            for minion_id, low_states in metadata.items():
                if not isinstance(low_states, list):
                    continue
                for low_state in low_states:
                    low_state['minion'] = minion_id
                    self._create_resource('{}|{}'.format(minion_id,
                                                         low_state['__id__']),
                                          '{} {}'.format(low_state['state'],
                                                         low_state['__id__']),
                                          'salt_lowstate',
                                          metadata=low_state)
        elif kind == 'salt_minion':
            for minion_id, minion_data in metadata.items():
                self._create_resource(minion_id,
                                      minion_id,
                                      'salt_minion',
                                      metadata=minion_data)
        elif kind == 'salt_service':
            for minion_name, minion_data in metadata.items():
                if not isinstance(minion_data, dict):
                    continue
                for service_name, service in minion_data.items():
                    if service_name not in settings.RECLASS_SERVICE_BLACKLIST:
                        for role_name, role in service.items():
                            if role_name not in settings.RECLASS_ROLE_BLACKLIST:
                                service_key = '{}-{}'.format(service_name,
                                                             role_name)
                                self._create_resource('{}|{}'.format(minion_name, service_key),
                                                      service_key,
                                                      'salt_service',
                                                      metadata=minion_data)

    def process_relation_metadata(self):
        # Define relationships between services and minions
        for resource_id, resource in self.resources.get('salt_service',
                                                        {}).items():
            self._create_relation(
                'on_salt_minion',
                resource_id,
                resource_id.split('|')[0])

        # Define relationships between lowstates and minions
        for resource_id, resource in self.resources.get('salt_lowstate',
                                                        {}).items():
            self._create_relation(
                'on_salt_minion',
                resource_id,
                resource['metadata']['minion'])
            split_service = resource['metadata']['__sls__'].split('.')
            self._create_relation(
                'contains_salt_lowstate',
                '{}|{}-{}'.format(resource['metadata']['minion'],
                                  split_service[0], split_service[1]),
                resource_id)

        for resource_id, resource in self.resources.get('salt_job',
                                                        {}).items():
            self._create_relation(
                'by_salt_user',
                resource_id,
                resource['metadata']['User'])
            for minion_id, result in resource['metadata'].get('Result',
                                                              {}).items():
                self._create_relation(
                    'on_salt_minion',
                    resource_id,
                    minion_id)
                if type(result) is list:
                    logger.error(result[0])
                else:
                    for state_id, state in result.items():
                        if '__id__' in state:
                            result_id = '{}|{}'.format(minion_id,
                                                       state['__id__'])
                            self._scrape_relation(
                                'contains_salt_lowstate',
                                resource_id,
                                result_id)
