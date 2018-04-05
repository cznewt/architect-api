# -*- coding: utf-8 -*-

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from architect.manager.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)

DEFAULT_RESOURCES = [
    'az_resource_group',
    '__all__'
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

    def __init__(self, **kwargs):
        super(MicrosoftAzureClient, self).__init__(**kwargs)

    def auth(self):

        credentials = ServicePrincipalCredentials(
            client_id=self.metadata['client_id'],
            secret=self.metadata['client_secret'],
            tenant=self.metadata['tenant_id']
        )

        self.api = ResourceManagementClient(credentials, self.metadata['subscription_id'])

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
        return 'unknown'

    def process_relation_metadata(self):
        
        for resource_id, resource in self.resources.get('az_resource_group', {}).items():
            pass

    def get_resource_metadata(self, kind):
        logger.info("Getting {} resources".format(kind))
        response = []
        if kind == 'az_resource_group':
            response = self.api.resource_groups.list(raw=True)
        elif kind == '__all__':
            response =  self.api.resources.list(raw=True)
        return response

    def process_resource_metadata(self, kind, metadata):
        if kind == 'az_resource_group':
            for item in metadata:
                resource = item.__dict__
                resource['properties'] = resource['properties'].__dict__
                logger.info(resource)
                self._create_resource(resource['id'],
                                      resource['name'],
                                      'az_resource_group',
                                      metadata=resource)
        elif kind == '__all__':
            for item in metadata:
                resource = item.__dict__
                if resource.get('system_assigned', None) != None:
                    resource['system_assigned'] = resource['system_assigned'].__dict__
                if resource.get('sku', None) != None:
                    resource['sku'] = resource['sku'].__dict__
                if resource.get('identity', None) != None:
                    resource['identity'] = resource['identity'].__dict__
                if resource['type'] not in RESOURCE_MAP:
                    logger.info(resource['type'])
                self._create_resource(resource['id'],
                                      resource['name'],
                                      RESOURCE_MAP[resource['type']],
                                      metadata=resource)
