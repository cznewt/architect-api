
import time
from architect import utils
from architect.manager.models import Resource, Manager


class BaseClient(object):

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.metadata = dict(kwargs['metadata'])
        self.kind = kwargs['engine']
        self.resources = {}
        self.resource_types = {}
        self.relations = {}
        self.timestamp = int(time.time())
        self._reverse_map = None
        self._schema = utils.get_resource_schema(self.kind)

    def get_resource_status(self, name, metadata):
        raise NotImplementedError

    def update_resources(self, resources=None):
        raise NotImplementedError

    def save(self):
        manager = Manager.objects.get(name=self.name)
        for resource_type, resources in self.resources.items():
            for resource_name, resource in resources.items():
                res, created = Resource.objects.get_or_create(uid=resource['uid'], manager=manager)
                if created:
                    res.name = resource['name']
                    res.kind = resource_type
                    res.manager = manager
                    res.metadata = resource['metadata']
                    res.status = self.get_resource_status(resource_type,
                                                          resource['metadata'])
                    res.save()

    def to_dict(self):
        return {
            'name': self.name,
            'kind': self.kind,
            'timestamp': self.timestamp,
            'resource_types': self._get_resource_types(),
            'resources': self.resources,
            'relation_types': self._get_relation_types(),
            'relations': self.relations,
        }

    def _get_resource_types(self):
        res_map = {}
        for resource_name, resource in self.resources.items():
            res_map[resource_name] = self._schema['resource'][resource_name]
        return res_map

    def _get_relation_types(self):
        rel_map = {}
        for relation_name, relation in self.relations.items():
            rel_map[relation_name] = self._schema['relation'][relation_name]
        return rel_map

    def _get_resource_mapping(self):
        if self._reverse_map is None:
            self._reverse_map = {}
            for resource_name, resource in self._schema['resource'].items():
                self._reverse_map[resource['resource']] = resource_name
        return self._reverse_map

    def _create_resource(self, uid, name, kind, metadata={}):
        if kind not in self.resources:
            self.resources[kind] = {}
        self.resources[kind][uid] = {
            'uid': uid,
            'name': name,
            'kind': kind,
            'metadata': metadata,
        }

    def _create_relation(self, kind, source, target):
        if kind not in self.relations:
            self.relations[kind] = []
        self.relations[kind].append({
            'source': source,
            'target': target,
            'kind': kind,
        })
