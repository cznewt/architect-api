
import json
import requests
from celery.utils.log import get_logger
from architect import utils
from architect.monitor.models import Monitor, Resource

logger = get_logger(__name__)


class BaseClient(object):

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.metadata = kwargs.get('metadata', {})
        self.kind = kwargs.get('engine')
        self.base_url = self.metadata['auth_url']
        self.user = self.metadata.get('user', None)
        self.password = self.metadata.get('password', None)
        self.queries = kwargs.get('queries', [])
        self.moment = kwargs.get('moment', None)
        self.start = kwargs.get('start', None)
        self.end = kwargs.get('end', None)
        self.step = kwargs.get('step', None)
        self.verify = False
        self._schema = utils.get_resource_schema(self.kind)

    def _create_resource(self, uid, name, kind, metadata={}):
        if kind not in self.resources:
            self.resources[kind] = {}
        self.resources[kind][uid] = {
            'uid': uid,
            'name': name,
            'kind': kind,
            'metadata': metadata,
        }

    def save(self):
        monitor = Monitor.objects.get(name=self.name)
        for resource_type, resources in self.resources.items():
            for resource_name, resource in resources.items():
                res, created = Resource.objects.get_or_create(uid=resource['uid'],
                                                              monitor=monitor)
                if created:
                    res.name = resource['name']
                    res.kind = resource_type
                    res.metadata = resource['metadata']
                    res.status = self.get_resource_status(resource_type,
                                                          resource['metadata'])
                    res.save()

    def log_error(self, flag, message):
        logger.error('Prometheus API replied with '
                     'error {}: {}'.format(flag, message))

    def check_status(self):
        raise NotImplementedError

    def get_http_series_params(self):
        return json.loads(requests.get(self.get_series_url(),
                                       params=self.get_series_params(),
                                       verify=self.verify).text)

    def get_http_series_data(self):
        return json.loads(requests.get(self.get_series_url(),
                                       data=json.dumps(self.get_series_params()),
                                       verify=self.verify).text)

    def process_instant(self, data):
        raise NotImplementedError

    def get_instant_url(self):
        raise NotImplementedError

    def process_range(self, data):
        raise NotImplementedError

    def get_range_url(self):
        raise NotImplementedError

    def get_range(self):
        data = json.loads(requests.get(self._url(), verify=False).text)
        return self.process_range(data)

    def get_http_instant_params(self):
        return json.loads(requests.get(self.get_instant_url(),
                                       params=self.get_instant_params(),
                                       verify=self.verify).text)

    def get_http_instant_data(self):
        return json.loads(requests.get(self.get_instant_url(),
                                       data=json.dumps(self.get_instant_params()),
                                       verify=self.verify).text)

    def get_http_range_params(self):
        return json.loads(requests.get(self.get_range_url(),
                                       params=self.get_range_params(),
                                       verify=self.verify).text)

    def get_http_range_data(self):
        return json.loads(requests.get(self.get_range_url(),
                                       data=json.dumps(self.get_range_params()),
                                       verify=self.verify).text)
