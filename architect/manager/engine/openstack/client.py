# -*- coding: utf-8 -*-

import os
import pyaml
import tempfile
import os_client_config
from os_client_config import cloud_config
from keystoneauth1.exceptions.connection import ConnectFailure
from heatclient.exc import HTTPBadRequest
from architect.manager.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)

NETWORK_RESOURCES = [
    'os_router',
    'os_floating_ip',
    'os_network',
    'os_subnet',
    'os_port'
]


class OpenStackClient(BaseClient):

    def __init__(self, **kwargs):
        self.scope = kwargs.get('metadata', {}).get('scope', 'local')
        super(OpenStackClient, self).__init__(**kwargs)

    def auth(self):
        status = True
        try:
            config_file, filename = tempfile.mkstemp()
            config_content = {
                'clouds': {self.name: self.metadata}
            }
            os.write(config_file, pyaml.dump(config_content).encode())
            os.close(config_file)
            self.cloud = os_client_config.config \
                .OpenStackConfig(config_files=[filename]) \
                .get_one_cloud(cloud=self.name)
            os.remove(filename)
            self.identity_api = self._get_client('identity')
            self.compute_api = self._get_client('compute')
            self.network_api = self._get_client('network')
            self.orch_api = self._get_client('orchestration')
            self.image_api = self._get_client('image')
            self.volume_api = self._get_client('volume')
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
                    'os_server',
                    # 'os_security_group',
                    'os_key_pair',
                    'os_flavor',
                    'os_image',
                    'os_volume',
                    'os_network',
                    'os_subnet',
                    'os_router',
                    'os_floating_ip',
                    'os_port',
                    # 'os_stack',
                ]
                if self.scope == 'global':
                    resources += ['os_project', 'os_user']
                    resources += ['os_aggregate', 'os_hypervisor']

            for resource in resources:
                metadata = self.get_resource_metadata(resource)
                self.process_resource_metadata(resource, metadata)
                count = len(self.resources.get(resource, {}))
                logger.info("Processed {} {} resources".format(count,
                                                               resource))
            self.process_relation_metadata()

    def process_resource_metadata(self, kind, metadata):
        if kind == 'os_hypervisor':
            for item in metadata:
                resource = item.to_dict()
                self._create_resource(resource['service']['host'],
                                      resource['hypervisor_hostname'],
                                      'os_hypervisor',
                                      metadata=resource)
        elif kind == 'os_key_pair':
            for item in metadata:
                resource = item.to_dict()['keypair']
                self._create_resource(resource['name'],
                                      resource['name'],
                                      'os_key_pair',
                                      metadata=resource)
        elif kind == 'os_image':
            for item in metadata:
                resource = item.__dict__['__original__']
                self._create_resource(resource['id'],
                                      resource['name'],
                                      'os_image',
                                      metadata=resource)
        else:
            for item in metadata:
                if kind in NETWORK_RESOURCES:
                    resource = item
                else:
                    resource = item.to_dict()
                uid = resource.get('id', resource.get('name'))
                name = resource.get('name',
                                    resource.get('stack_name',
                                                 resource.get('id')))
                self._create_resource(uid,
                                      name,
                                      kind,
                                      metadata=resource)

    def get_resource_metadata(self, kind):
        logger.info("Getting {} resources".format(kind))
        # keystone resources
        if kind == 'os_user':
            response = self.identity_api.get('/users')
        elif kind == 'os_project':
            response = self.identity_api.tenants.list()
        # nova resources
        elif kind == 'os_aggregate':
            response = self.compute_api.aggregates.list()
        elif kind == 'os_key_pair':
            response = self.compute_api.keypairs.list()
        elif kind == 'os_flavor':
            response = self.compute_api.flavors.list()
        elif kind == 'os_hypervisor':
            response = self.compute_api.hypervisors.list()
        elif kind == 'os_server':
            if self.scope == 'global':
                search_opts = {'all_tenants': 1}
            else:
                search_opts = None
            response = self.compute_api.servers.list(
                search_opts=search_opts)
        elif kind == 'os_security_group':
            if self.scope == 'global':
                search_opts = {'all_tenants': 1}
            else:
                search_opts = None
            response = self.compute_api.security_groups.list(
                search_opts=search_opts)
        elif kind == 'os_volume':
            response = self.volume_api.volumes.list()
        elif kind == 'os_image':
            response = self.image_api.images.list()
        # neutron resources
        elif kind == 'os_router':
            response = self.network_api.list_routers().get('routers')
        elif kind == 'os_floating_ip':
            response = self.network_api.list_floatingips().get('floatingips')
        elif kind == 'os_network':
            response = self.network_api.list_networks().get('networks')
        elif kind == 'os_subnet':
            response = self.network_api.list_subnets().get('subnets')
        elif kind == 'os_port':
            response = self.network_api.list_ports().get('ports')
        # heat resources
        elif kind == 'os_stack':
            response = []
            if self.scope == 'global':
                search_opts = {'all_tenants': 1}
            else:
                search_opts = None
            stacks = self.orch_api.stacks.list(
                search_opts=search_opts)
            for stack in stacks:
                resource = stack.to_dict()
                resource['resources'] = []
                try:
                    resources = self.orch_api.resources.list(stack['id'],
                                                             nested_depth=2)
                    for stack_resource in resources:
                        resource['resources'].append(stack_resource.to_dict())
                except HTTPBadRequest as exception:
                    logger.error(exception)
                response.append(resource)
        return response

    def get_resource_status(self, kind, metadata):
        if not isinstance(metadata, dict):
            return 'unknown'
        if metadata.get('status', 'ACTIVE'):
            return 'active'
        return 'unknown'

    def process_relation_metadata(self):
        # Define relationships between project and all namespaced resources.
        for resource_type, resource_dict in self.resources.items():
            for resource_id, resource in resource_dict.items():
                if 'tenant_id' in resource['metadata']:
                    self._create_relation(
                        'in_os_project',
                        resource_id,
                        resource['metadata']['tenant_id'])
                elif 'project' in resource['metadata']:
                    self._create_relation(
                        'in_os_project',
                        resource_id,
                        resource['metadata']['project'])

        for resource_id, resource in self.resources.get('os_stack',
                                                        {}).items():
            for ext_res in resource['metadata']['resources']:
                if ext_res['resource_type'] in self._get_resource_mapping():
                    self._create_relation(
                        'os_stack-{}'.format(
                            self._get_resource_mapping()[ext_res['resource_type']]),
                        resource_id,
                        ext_res['physical_resource_id'])

        # Define relationships between aggregate zone and all hypervisors.
        for resource_id, resource in self.resources.get('os_aggregate',
                                                        {}).items():
            for host in resource['metadata']['hosts']:
                self._create_relation(
                    'in_os_aggregate',
                    host,
                    resource_id)

        for resource_id, resource in self.resources.get('os_floating_ip',
                                                        {}).items():
            if resource['metadata'].get('port_id', None) is not None:
                self._create_relation(
                    'use_os_port',
                    resource_id,
                    resource['metadata']['port_id'])

        for resource_id, resource in self.resources.get('os_port',
                                                        {}).items():
            self._create_relation(
                'in_os_network',
                resource_id,
                resource['metadata']['network_id'])
            if resource['metadata']['device_id'] is not None:
                self._create_relation(
                    'use_os_port',
                    resource['metadata']['device_id'],
                    resource_id)
            if self.scope == 'global':
                if resource['metadata'].get('binding:host_id', False):
                    self._create_relation(
                        'on_os_hypervisor',
                        resource_id,
                        resource['metadata']['binding:host_id'])

        for resource_id, resource in self.resources.get('os_server',
                                                        {}).items():
            if self.scope == 'global':
                self._create_relation(
                    'on_os_hypervisor',
                    resource_id,
                    resource['metadata']['OS-EXT-SRV-ATTR:host'])

            self._create_relation(
                'use_os_flavor',
                resource_id,
                resource['metadata']['flavor']['id'])

            if resource['metadata']['image'] != '':
                if resource['metadata']['image'].get('id', None) is not None:
                    self._create_relation(
                        'use_os_image',
                        resource_id,
                        resource['metadata']['image']['id'])
            if resource['metadata']['key_name'] != '':
                self._create_relation(
                    'use_os_key_pair',
                    resource_id,
                    resource['metadata']['key_name'])

        for resource_id, resource in self.resources.get('os_subnet',
                                                        {}).items():
            self._create_relation(
                'in_os_network',
                resource_id,
                resource['metadata']['network_id'])
