# -*- coding: utf-8 -*-

from architect.manager.client import BaseClient
import homeassistant.remote as remote
from homeassistant.exceptions import HomeAssistantError
from celery.utils.log import get_logger

logger = get_logger(__name__)

DEFAULT_RESOURCES = [
    'ha_entity',
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
        return 'active'

    def get_resource_metadata(self, kind):
        logger.info("Getting {} resources".format(kind))
        response = []
        if kind == 'ha_entity':
            response = remote.get_states(self.api)
        return response

    def process_resource_metadata(self, kind, metadata):
        if kind == 'ha_entity':
            self._create_resource('group.ungrouped_resources',
                                  'Ungrouped resources',
                                  'ha_view',
                                  metadata={'attributes': {'entity_id':[]}})
            for resource in metadata:
                metadata = resource.as_dict()
                domain, entity = metadata['entity_id'].split('.')
                if 'ha_{}'.format(domain) in self.resource_type_list():
                    if metadata['attributes'].get('view', False):
                        domain = 'view'
                    if 'last_changed' in metadata:
                        metadata['last_changed'] = metadata['last_changed'].isoformat()
                    if 'last_updated' in metadata:
                        metadata['last_updated'] = metadata['last_updated'].isoformat()
                    self._create_resource(metadata['entity_id'],
                                          metadata['attributes'].get('friendly_name', metadata['entity_id'].split('.')[1]),
                                          'ha_{}'.format(domain),
                                          metadata=metadata)
                else:
                    logger.error('{} not supported.'.format(domain))
                    pass

    def process_relation_metadata(self):
        grouped_resources = []
        for resource_id, resource in self.resources.get('ha_view', {}).items():
            for group in resource['metadata']['attributes']['entity_id']:
                self._create_relation(
                    'in_view',
                    group,
                    resource_id)
                grouped_resources.append(group)
        for resource_id, resource in self.resources.get('ha_group', {}).items():
            for group in resource['metadata']['attributes']['entity_id']:
                self._create_relation(
                    'in_group',
                    group,
                    resource_id)
                grouped_resources.append(group)
        for kind, resources in self.resources.items():
            if kind not in ['ha_view']:
                for resource_id, resource in resources.items():
                    if resource_id not in grouped_resources:
                        self._create_relation(
                            'in_view',
                            'group.ungrouped_resources',
                            resource_id)

    def get_resource_action_fields(self, resource, action):
        fields = {}
        if resource.kind == 'ha_script':
            pass
        elif resource.kind == 'ha_light':
            pass
        return fields

    def process_resource_action(self, resource, action, data):
        domain = resource.uid.split('.')[0]
        if resource.kind == 'ha_script':
            if action == 'execute_script':
                if self.auth():
                    remote.call_service(self.api, domain, 'turn_on', {'entity_id': resource.uid})
        if resource.kind == 'ha_light':
            if action == 'turn_on_light':
                if self.auth():
                    remote.call_service(self.api, domain, 'turn_on', {'entity_id': resource.uid})
            elif action == 'turn_off_light':
                if self.auth():
                    remote.call_service(self.api, domain, 'turn_off', {'entity_id': resource.uid})
