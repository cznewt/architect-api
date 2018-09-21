# -*- coding: utf-8 -*-

import yaml
from django import forms

import msrest
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.containerservice import ContainerServiceClient

from architect.manager.client import BaseClient
from architect.manager.models import Manager
from celery.utils.log import get_logger
import json


logger = get_logger(__name__)

DEFAULT_RESOURCES = [
    'az_subscription',
    'az_location',
    'az_resource_group',
    'az_managed_cluster',
    'az_virtual_machine_size',
    'az_virtual_machine',
    'az_network',
    'az_subnet',
#    'az_network_interface',
#    '__all__'
]

RESOURCE_MAP = {
    'Microsoft.ContainerRegistry/registries': 'az_registry',
    'Microsoft.ContainerRegistry/registries/replications': 'az_registry_replication',
    'Microsoft.Compute/availabilitySets': 'az_availability_set',
    'Microsoft.Compute/disks': 'az_disk',
    'Microsoft.Compute/images': 'az_image',
    'Microsoft.Compute/virtualMachineScaleSets': 'az_virtual_machine_scale_set',
    'Microsoft.Compute/virtualMachines': 'az_virtual_machine',
    'Microsoft.Compute/virtualMachines/extensions': 'az_virtual_machine_extension',
    'Microsoft.ContainerService/managedClusters': 'az_kubernetes_cluster',
    'Microsoft.Network/dnszones': 'az_dns_zone',
    'Microsoft.Network/virtualNetworks': 'az_network',
    'Microsoft.Network/routeTables': 'az_route_table',
    'Microsoft.Network/loadBalancers': 'az_load_balancer',
    'Microsoft.Network/networkInterfaces': 'az_network_interface',
    'Microsoft.Network/networkSecurityGroups': 'az_security_group',
    'Microsoft.Network/publicIPAddresses': 'az_public_ip_address',
    'Microsoft.OperationalInsights/workspaces': 'az_workspace',
    'Microsoft.OperationsManagement/solutions': 'az_solution',
    'Microsoft.Storage/storageAccounts': 'az_storage_account',
}

class MicrosoftAzureClient(BaseClient):

    credentials = None
    size_location = {}
    network = []


    def __init__(self, **kwargs):
        super(MicrosoftAzureClient, self).__init__(**kwargs)

    def auth(self):

        if self.credentials is None:

            self.credentials = ServicePrincipalCredentials(
                client_id=self.metadata['client_id'],
                secret=self.metadata['client_secret'],
                tenant=self.metadata['tenant_id']
            )

            self.resource_api = ResourceManagementClient(self.credentials, self.metadata['subscription_id'])
            self.compute_api = ComputeManagementClient(self.credentials, self.metadata['subscription_id'])
            self.network_api = NetworkManagementClient(self.credentials, self.metadata['subscription_id'])
            self.container_service_api = ContainerServiceClient(self.credentials, self.metadata['subscription_id'])
            self.subscription_api = SubscriptionClient(self.credentials)

        return True

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
        if kind == 'az_resource_group':
            state = metadata.get('properties', {}).get('provisioning_state', '')
            if state == 'Succeeded':
                return 'active'
        elif kind in ['az_virtual_machine_size', 'az_location']:
            return 'active'
        elif kind in ['az_virtual_machine', 'az_managed_cluster', 'az_network', 'az_subnet']:
            state = metadata.get('provisioning_state', '')
            if state == 'Succeeded':
                return 'active'
        elif kind == 'az_subscription':
            if metadata.get('state', '') == 'Enabled':
                return 'active'
        return 'unknown'

    def process_relation_metadata(self):

        for resource_id, resource in self.resources.get('az_managed_cluster', {}).items():
            self._create_relation(
                'in_resource_group',
                resource_id,
                self.get_group_id_from_resource_id(resource_id))
        for resource_id, resource in self.resources.get('az_subnet', {}).items():
            self._create_relation(
                'in_resource_group',
                resource_id,
                self.get_group_id_from_resource_id(resource_id))
        for resource_id, resource in self.resources.get('az_network', {}).items():
            self._create_relation(
                'in_resource_group',
                resource_id,
                self.get_group_id_from_resource_id(resource_id))
            for subnet in resource['metadata'].get('subnets', []):
                self._create_relation(
                    'in_network',
                    subnet['id'],
                    resource_id)
        for resource_id, resource in self.resources.get('az_virtual_machine', {}).items():
            self._create_relation(
                'in_resource_group',
                resource_id,
                self.get_group_id_from_resource_id(resource_id))
            self._create_relation(
                'has_size',
                resource_id,
                resource['metadata']['hardware_profile']['vm_size'])
            self._create_relation(
                'at_location',
                resource_id,
                resource['metadata']['location'])
        for location, sizes in self.size_location.items():
            for size in sizes:
                self._create_relation(
                    'at_location',
                    size,
                    location)
        for resource_id, resource in self.resources.get('az_resource_group', {}).items():
            self._create_relation(
                'at_location',
                resource_id,
                resource['metadata']['location'])

    def get_resource_metadata(self, kind):
        logger.info("Getting {} resources".format(kind))
        response = []
        if kind == 'az_subscription':
            response = self.subscription_api.subscriptions.list(raw=True)
        elif kind == 'az_managed_cluster':
            for subscription in self.subscription_api.subscriptions.list(raw=True):
                for item in self.container_service_api.managed_clusters.list(subscription.subscription_id, raw=True):
                    response.append(item)
        elif kind == 'az_location':
            for subscription in self.subscription_api.subscriptions.list(raw=True):
                for item in self.subscription_api.subscriptions.list_locations(subscription.subscription_id, raw=True):
                    response.append(item)
        elif kind == 'az_resource_group':
            for subscription in self.subscription_api.subscriptions.list(raw=True):
                for item in self.resource_api.resource_groups.list(raw=True):
                    response.append(item)
        elif kind == 'az_subnet':
            for network in self.network:
                for subnet in self.network_api.subnets.list(resource_group_name=network[0], virtual_network_name=network[1], raw=True):
                    response.append(subnet)
        elif kind == 'az_network_interface':
            for network_interface in self.network_api.network_interfaces.list(raw=True):
                response.append(network_interface)
                logger.info(network_interface)
        elif kind == 'az_network':
            for subscription in self.subscription_api.subscriptions.list(raw=True):
                for virtual_network in self.network_api.virtual_networks.list_all(raw=True):
                    response.append(virtual_network)
                    logger.info(virtual_network.id.split('/')[4])
                    self.network.append((virtual_network.id.split('/')[4], virtual_network.name,))
        elif kind == 'az_virtual_machine':
            for subscription in self.subscription_api.subscriptions.list(raw=True):
                for virtual_machine in self.compute_api.virtual_machines.list_all(raw=True):
                    response.append(virtual_machine)
        elif kind == 'az_virtual_machine_size':
            for subscription in self.subscription_api.subscriptions.list(raw=True):
                size_names = {}
                for location in self.subscription_api.subscriptions.list_locations(subscription.subscription_id, raw=True):
                    try:
                        for size in self.compute_api.virtual_machine_sizes.list(location.name):
                            if not location.name in self.size_location:
                                self.size_location[location.name] = []
                            self.size_location[location.name].append(size.name)
                            size_names[size.name] = size
                    except msrest.exceptions.ClientException as error:
                        logger.error(error)
            for size_name, size in size_names.items():
                response.append(size)
        elif kind == '__all__':
            response = self.resource_api.resources.list(raw=True)
        return response

    def process_resource_metadata(self, kind, metadata):
        if kind == 'az_resource_group':
            for item in metadata:
                resource = item.__dict__
                resource['properties'] = resource['properties'].__dict__
                self._create_resource(resource['id'],
                                      resource['name'],
                                      kind,
                                      metadata=resource)
        elif kind == 'az_virtual_machine_size':
            for item in metadata:
                resource = item.__dict__
                self._create_resource(resource['name'],
                                      resource['name'],
                                      kind,
                                      metadata=resource)
        elif kind == 'az_subscription':
            for item in metadata:
                resource = item.__dict__
                resource['subscription_policies'] = resource['subscription_policies'].__dict__
                self._create_resource(resource['id'],
                                      resource['display_name'],
                                      kind,
                                      metadata=resource)
        elif kind == 'az_managed_cluster':
            for item in metadata:
                resource = item.__dict__
                resource['network_profile'] = resource.pop('network_profile').__dict__
                if resource['aad_profile'] is not None:
                    resource['aad_profile'] = resource.pop('aad_profile').__dict__
                if resource['linux_profile'] is not None:
                    resource['linux_profile'] = resource.pop('linux_profile').__dict__
                    resource['linux_profile']['ssh'] = resource['linux_profile'].pop('ssh').__dict__
                    public_keys = []
                    for public_key in resource['linux_profile']['ssh'].pop('public_keys'):
                        public_keys.append(public_key.__dict__)
                    resource['linux_profile']['ssh']['public_keys'] = public_keys
                resource['service_principal_profile'] = resource.pop('service_principal_profile').__dict__
                if resource['addon_profiles'] is not None:
                    addon_profiles = []
                    for res in resource.pop('addon_profiles'):
                        if not isinstance(res, str):
                            res = res.__dict__
                        addon_profiles.append(res)
                    resource['addon_profiles'] = addon_profiles
                if resource['agent_pool_profiles'] is not None:
                    agent_pool_profiles = []
                    for res in resource.pop('agent_pool_profiles'):
                        res = res.__dict__
                        agent_pool_profiles.append(res)
                    resource['agent_pool_profiles'] = agent_pool_profiles
                self._create_resource(resource['id'],
                                      resource['name'],
                                      kind,
                                      metadata=resource)
        elif kind == 'az_location':
            for item in metadata:
                resource = item.__dict__
                self._create_resource(resource['name'],
                                      resource['display_name'],
                                      kind,
                                      metadata=resource)
        elif kind == 'az_virtual_machine':
            for item in metadata:
                resource = item.__dict__
                resource['hardware_profile'] = resource.pop('hardware_profile').__dict__
                resource['storage_profile'] = resource.pop('storage_profile').__dict__
                if resource['storage_profile']['image_reference'] is not None:
                    resource['storage_profile']['image_reference'] = resource['storage_profile'].pop('image_reference').__dict__
                data_disks = []
                if 'data_disks' in resource['storage_profile']:
                    for data_disk in resource['storage_profile'].pop('data_disks'):
                        data_disk = data_disk.__dict__
                        if data_disk['managed_disk'] is not None:
                            data_disk['managed_disk'] = data_disk.pop('managed_disk').__dict__
                        if data_disk['vhd'] is not None:
                            data_disk['vhd'] = data_disk.pop('vhd').__dict__
                        data_disks.append(data_disk)
                    resource['storage_profile']['data_disks'] = data_disks
                resource['storage_profile']['os_disk'] = resource['storage_profile'].pop('os_disk').__dict__
                if resource['storage_profile']['os_disk']['managed_disk'] is not None:
                    resource['storage_profile']['os_disk']['managed_disk'] = resource['storage_profile']['os_disk'].pop('managed_disk').__dict__
                if resource['storage_profile']['os_disk']['image'] is not None:
                    resource['storage_profile']['os_disk']['image'] = resource['storage_profile']['os_disk'].pop('image').__dict__
                if resource['storage_profile']['os_disk']['vhd'] is not None:
                    resource['storage_profile']['os_disk']['vhd'] = resource['storage_profile']['os_disk'].pop('vhd').__dict__
                network_interfaces = []
                resource['network_profile'] = resource.pop('network_profile').__dict__
                for network_interface in resource['network_profile'].pop('network_interfaces'):
                    network_interfaces.append(network_interface.__dict__)
                resource['network_profile']['network_interfaces'] = network_interfaces
                if resource['diagnostics_profile'] is not None:
                    resource['diagnostics_profile'] = resource.pop('diagnostics_profile').__dict__
                    resource['diagnostics_profile']['boot_diagnostics'] = resource['diagnostics_profile'].pop('boot_diagnostics').__dict__
                resource['os_profile'] = resource.pop('os_profile').__dict__
                if 'linux_configuration' in resource['os_profile']:
                    resource['os_profile']['linux_configuration'] = resource['os_profile'].pop('linux_configuration').__dict__
                    resource['os_profile']['linux_configuration']['ssh'] = resource['os_profile']['linux_configuration'].pop('ssh').__dict__
                    public_keys = []
                    for public_key in resource['os_profile']['linux_configuration']['ssh'].pop('public_keys'):
                        public_keys.append(public_key.__dict__)
                    resource['os_profile']['linux_configuration']['ssh']['public_keys'] = public_keys
                if resource['resources'] is not None:
                    resources = []
                    for res in resource.pop('resources'):
                        resources.append(res.__dict__)
                    resource['resources'] = resources
                if resource['availability_set'] is not None:
                    resource['availability_set'] = resource.pop('availability_set').__dict__
                self._create_resource(resource['id'],
                                    resource['name'],
                                    kind,
                                    metadata=resource)
        elif kind == 'az_network':
            for item in metadata:
                resource = item.__dict__
                resource['address_space'] = resource.pop('address_space').__dict__
                if 'network_security_group' in resource:
                    resource['network_security_group'] = resource.pop('network_security_group').__dict__
                if resource['dhcp_options'] is not None:
                    resource['dhcp_options'] = resource.pop('dhcp_options').__dict__
                if resource['subnets'] is not None:
                    subnets = []
                    for res in resource.pop('subnets'):
                        res = res.__dict__
                        if res['route_table'] is not None:
                            res['route_table'] = res.pop('route_table').__dict__
                        if 'network_security_group' in res and res['network_security_group'] is not None:
                            res['network_security_group'] = res.pop('network_security_group').__dict__
                        if res['ip_configurations'] is not None:
                            ip_configurations = []
                            for ress in res.pop('ip_configurations'):
                                ip_configurations.append(ress.__dict__)
                            res['ip_configurations'] = ip_configurations
                        subnets.append(res)
                    resource['subnets'] = subnets
                self._create_resource(resource['id'],
                                      resource['name'],
                                      kind,
                                      metadata=resource)
        elif kind == 'az_subnet':
            for item in metadata:
                resource = item.__dict__
                if resource['route_table'] is not None:
                    resource['route_table'] = resource.pop('route_table').__dict__
                if resource['network_security_group'] is not None:
                    resource['network_security_group'] = resource.pop('network_security_group').__dict__
                if resource['ip_configurations'] is not None:
                    ip_configurations = []
                    for res in resource.pop('ip_configurations'):
                        ip_configurations.append(res.__dict__)
                    resource['ip_configurations'] = ip_configurations
                self._create_resource(resource['id'],
                                      resource['name'],
                                      kind,
                                      metadata=resource)
        elif kind == '__all__':
            for item in metadata:
                resource = item.__dict__
                if resource.get('sku', None) != None:
                    resource['sku'] = resource['sku'].__dict__
                if resource.get('identity', None) != None:
                    identity = resource['identity'].__dict__
                    identity['type'] = identity['type'].__dict__
                    resource['identity'] = identity
                if resource['type'] not in RESOURCE_MAP:
                    logger.info(resource['type'])
                self._create_resource(resource['id'],
                                      resource['name'],
                                      RESOURCE_MAP[resource['type']],
                                      metadata=resource)

    def get_subscription_id_from_resource_id(self, id):
        parts = id.split('/')
        return '/'.join(parts[:3])

    def get_group_id_from_resource_id(self, id):
        parts = id.split('/')
        return '/'.join(parts[:5]).replace('/resourcegroups/', '/resourceGroups/')

    def get_group_name_from_resource_id(self, id):
        parts = id.split('/')
        return parts[4]

    def get_resource_action_fields(self, resource, action):
        fields = {}
        if resource.kind == 'az_managed_cluster':
            if action == 'create_manager':
                initial_name = resource.metadata['node_resource_group'].replace('MC_', '')
                fields['name'] = forms.CharField(label='New name',
                                                 help_text='Importing managed cluster <strong>{}</strong> from resource group <strong>{}</strong>.'.format(
                                                     resource.name, self.get_group_name_from_resource_id(resource.uid)),
                                                 initial=initial_name)
        return fields

    def process_resource_action(self, resource, action, data):
        if resource.kind == 'az_managed_cluster':
            if action == 'create_manager':
                if self.auth():
                    raw_data = self.container_service_api.managed_clusters.list_cluster_admin_credentials(self.get_group_name_from_resource_id(resource.uid),
                                                                                                          resource.metadata['name'])
                    for raw_kubeconfig in raw_data.kubeconfigs:
                        kubeconfig_yaml = raw_kubeconfig.value.decode()
                        kubeconfig = yaml.load(kubeconfig_yaml)
                        cluster = kubeconfig['clusters'][0]['cluster']
                        user = kubeconfig['users'][0]['user']
                        manager = Manager.objects.create(
                            name=data['name'],
                            engine="kubernetes",
                            metadata={
                                'user': user,
                                'cluster': cluster,
                                'engine': "kubernetes",
                                'scope': "global"
                            })
                        manager.save()
                        if manager.client().check_status():
                            manager.status = 'active'
                        else:
                            manager.status = 'error'
                        manager.save()
