# -*- coding: utf-8 -*-

from architect.manager.client import BaseClient
import homeassistant.remote as remote
from homeassistant.exceptions import HomeAssistantError
from celery.utils.log import get_logger

logger = get_logger(__name__)

DEFAULT_RESOURCES = [
    'hass_entity',
]


class HomeAssistantClient(BaseClient):

    def __init__(self, **kwargs):
        super(HomeAssistantClient, self).__init__(**kwargs)

    def auth(self):
        status = True
        try:
            self.api = remote.API(self.metadata['host'],
                                  self.metadata['password'],
                                  self.metadata.get('port', 8123),
                                  self.metadata.get('use_ssl', False))
        except HomeAssistantError as exception:
            logger.error(exception)
            status = False
        return status

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
        return 'unknown'

    def get_resource_metadata(self, kind):
        logger.info("Getting {} resources".format(kind))
        response = []
        if kind == 'hass_entity':
            response = remote.get_states(self.api)
        return response

    def process_resource_metadata(self, kind, metadata):
        if kind == 'hass_entity':
            for resource in metadata:
                metadata = resource.as_dict()
                if 'last_changed' in metadata:
                    metadata['last_changed'] = metadata['last_changed'].isoformat()
                if 'last_updated' in metadata:
                    metadata['last_updated'] = metadata['last_updated'].isoformat()
                self._create_resource(metadata['entity_id'],
                                      metadata['entity_id'],
                                      'hass_entity',
                                      metadata=metadata)

    def process_relation_metadata(self):
        pass
