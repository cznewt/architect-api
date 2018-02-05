
import json
import requests
from architect import utils
from celery.utils.log import get_logger

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
