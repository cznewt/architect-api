
import json
import requests
from celery.utils.log import get_logger
from architect import utils
from architect.monitor.models import Monitor, Resource, Relationship

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
        if 'ca_cert' in self.metadata:
            with open('/tmp/{}-ca-cert.pem'.format(self.name), 'w') as ca_cert_file:
                ca_cert_file.write(self.metadata['ca_cert'])
            self.verify = '/tmp/{}-ca-cert.pem'.format(self.name)
        else:
            self.verify = False
        if 'client_cert' in self.metadata and 'client_key' in self.metadata:
            with open('/tmp/{}-client-cert.pem'.format(self.name), 'w') as client_cert_file:
                client_cert_file.write(self.metadata['client_cert'])
            with open('/tmp/{}-client-key.pem'.format(self.name), 'w') as client_key_file:
                client_key_file.write(self.metadata['client_key'])
            self.cert = (
                '/tmp/{}-client-cert.pem'.format(self.name),
                '/tmp/{}-client-key.pem'.format(self.name),
            )
        else:
            self.cert = None

        self._schema = utils.get_resource_schema(self.kind)
        self.resources = {}
        self.resource_types = {}
        self.relations = {}

    def _create_resource(self, uid, name, kind, metadata={}):
        if kind not in self.resources:
            self.resources[kind] = {}
        self.resources[kind][uid] = {
            'uid': uid,
            'name': name,
            'kind': kind,
            'metadata': metadata,
        }

    def _create_relation(self, kind, source, target, metadata={}):
        if kind not in self.relations:
            self.relations[kind] = []
        self.relations[kind].append({
            'source': source,
            'target': target,
            'kind': kind,
            'metadata': metadata,
        })


    def save(self):
        monitor = Monitor.objects.get(name=self.name)
        for resource_type, resources in self.resources.items():
            for resource_name, resource in resources.items():
                res, created = Resource.objects.get_or_create(uid=resource['uid'],
                                                              monitor=monitor)
#                logger.info(resource)
                if created:
                    res.name = resource['name']
                    res.kind = resource_type
                    res.monitor = monitor
                    res.metadata = resource['metadata']
                    res.status = self.get_resource_status(resource_type,
                                                          resource['metadata'])
                    res.save()
                else:
                    if res.metadata != resource['metadata']:
                        res.metadata = resource['metadata']
                        res.status = self.get_resource_status(resource_type,
                                                              resource['metadata'])
                        res.save()

        res_list = {}
        res_list_rev = {}
        reses = Resource.objects.filter(monitor=monitor)
        for res in reses:
            res_list[res.uid] = res
            res_list_rev[res.id] = res.uid

        rel_list = {}
        rels = Relationship.objects.filter(monitor=monitor)
        for rel in rels:
            rel_list['{}-{}-{}'.format(res_list_rev[rel.source_id],
                                       rel.kind,
                                       res_list_rev[rel.target_id])] = rel
        for relation_type, relations in self.relations.items():
            logger.info('Processed {} {} relations'.format(len(relations),
                                                           relation_type))
            for relation in relations:
                if relation['source'] not in res_list:
                    logger.error('No resource with'
                                 ' uid {} found'.format(relation['source']))
                    print('No resource with'
                          ' uid {} found'.format(relation['source']))
                    continue
                if relation['target'] not in res_list:
                    logger.error('No resource with'
                                 ' uid {} found'.format(relation['target']))
                    print('No resource with'
                          ' uid {} found'.format(relation['target']))
                    continue
                rel_key = '{}-{}-{}'.format(relation['source'],
                                            relation['kind'],
                                            relation['target'])
                if rel_key not in rel_list:
                    resource = {
                        'kind': relation['kind'],
                        'monitor': monitor,
                        'source': res_list[relation['source']],
                        'target': res_list[relation['target']]
                    }
                    if 'metadata' in relation:
                        resource['metadata'] = relation['metadata']

                    res = Relationship.objects.create(**resource)
                    res.save()


    def log_error(self, flag, message):
        logger.error('Prometheus API replied with '
                     'error {}: {}'.format(flag, message))

    def get_resource_status(self, name, metadata):
        raise NotImplementedError

    def check_status(self):
        raise NotImplementedError

    def get_series_url(self):
        raise NotImplementedError

    def get_series_params(self):
        raise NotImplementedError

    def get_http_series_params(self):
        return json.loads(requests.get(self.get_series_url(),
                                       params=self.get_series_params(),
                                       cert=self.cert,
                                       verify=self.verify).text)

    def get_http_series_data(self):
        return json.loads(requests.get(self.get_series_url(),
                                       data=json.dumps(self.get_series_params()),
                                       cert=self.cert,
                                       verify=self.verify).text)

    def process_instant(self, data):
        raise NotImplementedError

    def get_instant_url(self):
        raise NotImplementedError

    def process_range(self, data):
        raise NotImplementedError

    def get_range_url(self):
        raise NotImplementedError

    def _url(self):
        raise NotImplementedError

    def get_range(self):
        data = json.loads(requests.get(self._url(),
                          cert=self.cert,
                          verify=self.verify).text)
        return self.process_range(data)

    def get_instant_params(self):
        raise NotImplementedError

    def get_http_instant_params(self):
        return json.loads(requests.get(self.get_instant_url(),
                                       params=self.get_instant_params(),
                                       cert=self.cert,
                                       verify=self.verify).text)

    def get_http_instant_data(self):
        return json.loads(requests.get(self.get_instant_url(),
                                       data=json.dumps(self.get_instant_params()),
                                       cert=self.cert,
                                       verify=self.verify).text)

    def get_range_params(self):
        raise NotImplementedError

    def get_http_range_params(self):
        return json.loads(requests.get(self.get_range_url(),
                                       params=self.get_range_params(),
                                       cert=self.cert,
                                       verify=self.verify).text)

    def get_http_range_data(self):
        return json.loads(requests.get(self.get_range_url(),
                                       data=json.dumps(self.get_range_params()),
                                       cert=self.cert,
                                       verify=self.verify).text)
