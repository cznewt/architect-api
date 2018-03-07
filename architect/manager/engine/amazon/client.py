# -*- coding: utf-8 -*-

import boto3
from architect.manager.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)

DEFAULT_RESOURCES = [
#    'ec2_image',
#    'ec2_elastic_ip',
    'ec2_instance',
    'ec2_internet_gateway',
    'ec2_subnet',
    'ec2_vpc',
    'ec2_key_pair',
    's3_bucket'
]


class AmazonWebServicesClient(BaseClient):

    def __init__(self, **kwargs):
        self.scope = kwargs.get('scope', 'local')
        super(AmazonWebServicesClient, self).__init__(**kwargs)

    def auth(self):
        self.ec2_client = boto3.resource('ec2',
            aws_access_key_id=self.metadata['aws_access_key_id'],
            aws_secret_access_key=self.metadata['aws_secret_access_key'],
            region_name=self.metadata['region']
        )
        self.s3_client = boto3.resource('s3',
            aws_access_key_id=self.metadata['aws_access_key_id'],
            aws_secret_access_key=self.metadata['aws_secret_access_key'],
            region_name=self.metadata['region']
        )
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
        if kind == 'ec2_instance':
            if metadata.get('State', {}).get('Name', '') == 'running':
                return 'active'
        elif kind == 'ec2_vpc':
            if metadata.get('State', '') == 'available':
                return 'active'
        return 'unknown'

    def process_relation_metadata(self):
        for resource_id, resource in self.resources.get('ec2_instance', {}).items():
            if 'VpcId' in resource['metadata']:
                if resource['metadata']['VpcId'] in self.resources.get('ec2_vpc', {}):
                    self._create_relation(
                        'in_ec2_vpc',
                        resource_id,
                        resource['metadata']['VpcId'])

            if 'KeyName' in resource['metadata']:
                if resource['metadata']['KeyName'] in self.resources.get('ec2_key_pair', {}):
                    self._create_relation(
                        'using_ec2_key_pair',
                        resource_id,
                        resource['metadata']['KeyName'])

            if 'SubnetId' in resource['metadata']:
                if resource['metadata']['SubnetId'] in self.resources.get('ec2_subnet', {}):
                    self._create_relation(
                        'in_ec2_subnet',
                        resource_id,
                        resource['metadata']['SubnetId'])

    def get_resource_metadata(self, kind):
        logger.info("Getting {} resources".format(kind))
        response = []
        if kind == 'ec2_elastic_ip':
            response = self.ec2_client.eips.all()
        elif kind == 'ec2_image':
            response = self.ec2_client.images.all()
        elif kind == 'ec2_instance':
            response = self.ec2_client.instances.all()
        elif kind == 'ec2_internet_gateway':
            response = self.ec2_client.internet_gateways.all()
        elif kind == 'ec2_key_pair':
            response = self.ec2_client.key_pairs.all()
        elif kind == 'ec2_subnet':
            response = self.ec2_client.subnets.all()
        elif kind == 'ec2_vpc':
            response = self.ec2_client.vpcs.all()
        elif kind == 's3_bucket':
            response = self.s3_client.buckets.all()
        return response

    def process_resource_metadata(self, kind, metadata):
        if kind == 'ec2_elastic_ip':
            for item in metadata:
                resource = item.meta.__dict__
                resource.pop('resource_model')
                resource.pop('client')
                self._create_resource(resource['data']['InternetGatewayId'],
                                      resource['data']['InternetGatewayId'],
                                      'ec2_elastic_ip',
                                      metadata=resource['data'])
        elif kind == 'ec2_image':
            for item in metadata:
                resource = item.meta.__dict__
                resource.pop('resource_model')
                resource.pop('client')
                if 'Name' in resource['data']:
                    image_name = resource['data']['Name']
                else:
                    image_name = resource['data']['ImageId']
                self._create_resource(resource['data']['ImageId'],
                                      image_name,
                                      'ec2_image', metadata=resource['data'])
        elif kind == 'ec2_instance':
            for item in metadata:
                resource = item.meta.__dict__
                resource.pop('resource_model')
                resource.pop('client')
                try:
                    name = resource['data']['NetworkInterfaces'][0]['Association']['PublicDnsName']
                except Exception:
                    name = resource['data']['InstanceId']
                self._create_resource(resource['data']['InstanceId'],
                                      name,
                                      'ec2_instance', metadata=resource['data'])
        elif kind == 'ec2_internet_gateway':
            for item in metadata:
                resource = item.meta.__dict__
                resource.pop('resource_model')
                resource.pop('client')
                self._create_resource(resource['data']['InternetGatewayId'],
                                      resource['data']['InternetGatewayId'],
                                      'ec2_internet_gateway',
                                      metadata=resource['data'])
        elif kind == 'ec2_key_pair':
            for item in metadata:
                resource = item.meta.__dict__
                resource.pop('resource_model')
                resource.pop('client')
                self._create_resource(resource['data']['KeyName'],
                                      resource['data']['KeyName'],
                                      'ec2_key_pair',
                                      metadata=resource['data'])
        elif kind == 'ec2_subnet':
            for item in metadata:
                resource = item.meta.__dict__
                resource.pop('resource_model')
                resource.pop('client')
                self._create_resource(resource['data']['SubnetId'],
                                      resource['data']['SubnetId'],
                                      'ec2_subnet',
                                      metadata=resource['data'])
        elif kind == 'ec2_vpc':
            for item in metadata:
                resource = item.meta.__dict__
                resource.pop('resource_model')
                resource.pop('client')
                name = resource['data']['VpcId']
                for tag in resource['data'].get('Tags', {}):
                    if tag['Key'] == 'Name':
                        name = tag['Value']
                self._create_resource(resource['data']['VpcId'],
                                      name,
                                      'ec2_vpc',
                                      metadata=resource['data'])
        elif kind == 's3_bucket':
            for item in metadata:
                resource = item.meta.__dict__
                resource.pop('resource_model')
                resource.pop('client')
                self._create_resource(resource['data']['Name'],
                                      resource['data']['Name'],
                                      's3_bucket',
                                      metadata=resource['data'])
