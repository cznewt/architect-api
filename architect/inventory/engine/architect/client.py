# -*- coding: utf-8 -*-

from architect.inventory.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


class ArchitectClient(BaseClient):

    def __init__(self, **kwargs):
        super(ArchitectClient, self).__init__(**kwargs)

    def check_status(self):
        return False

    def inventory(self, resource=None):
        return {}

    def class_list(self, resource=None):
        return {}

    def parameter_list(self, resource=None):
        resource_list = {}
        return resource_list
