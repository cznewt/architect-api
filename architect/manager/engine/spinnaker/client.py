# -*- coding: utf-8 -*-

from architect.manager.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


class SpinnakerClient(BaseClient):

    def __init__(self, **kwargs):
        super(SpinnakerClient, self).__init__(**kwargs)

    def update_resources(self, resources=None):
        self.process_relation_metadata()

    def get_resource_status(self, kind, metadata):
        return 'unknown'

    def process_resource_metadata(self):
        pass

    def process_relation_metadata(self):
        pass
