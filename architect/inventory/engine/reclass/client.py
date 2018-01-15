# -*- coding: utf-8 -*-

from django.conf import settings
from reclass import get_storage
from reclass.core import Core
from architect.inventory.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


class ReclassClient(BaseClient):

    def __init__(self, **kwargs):
        super(ReclassClient, self).__init__(**kwargs)

    def inventory(self, resource=None):
        '''
        Get inventory nodes from reclass and their associated services
        and roles.
        '''
        storage = get_storage(self.metadata['storage_type'],
                              self.metadata['node_dir'],
                              self.metadata['class_dir'])
        reclass = Core(storage, None)
        if resource is None:
            return reclass.inventory()["nodes"]
        else:
            return reclass.inventory()["nodes"][resource]

    def class_list(self, resource=None):
        resource_list = {}
        for node_name, node in self.inventory().items():
            role_class = []
            for service_name, service in node['parameters'].items():
                if service_name not in settings.RECLASS_SERVICE_BLACKLIST:
                    for role_name, role in service.items():
                        if role_name not in settings.RECLASS_ROLE_BLACKLIST:
                            role_class.append('{}-{}'.format(service_name,
                                                             role_name))
            resource_list[node_name] = role_class
        if resource is None:
            return resource_list
        else:
            return {resource: resource_list[resource]}
