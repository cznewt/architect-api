# -*- coding: utf-8 -*-

from architect.manager.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


class AnsibleClient(BaseClient):

    def __init__(self, **kwargs):
        super(AnsibleClient, self).__init__(**kwargs)

    def update_resources(self, resources=None):
        self.process_relation_metadata()

    def get_resource_status(self, kind, metadata):
        return 'unknown'

    def process_relation_metadata(self):
        pass
