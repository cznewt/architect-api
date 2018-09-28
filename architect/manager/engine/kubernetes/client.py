# -*- coding: utf-8 -*-

import os
import base64
import pyaml
import tempfile
import pykube
from django import forms

from urllib.error import URLError
from requests.exceptions import HTTPError, ConnectionError
from architect.manager.client import BaseClient
from architect.monitor.models import Monitor
from celery.utils.log import get_logger

logger = get_logger(__name__)

DEFAULT_RESOURCES = [
    'k8s_cluster',
    'k8s_config_map',
    'k8s_cron_job',
    'k8s_daemon_set',
    'k8s_deployment',
    'k8s_endpoint',
    'k8s_event',
    'k8s_horizontal_pod_autoscaler',
    'k8s_ingress',
    'k8s_job',
    'k8s_persistent_volume',
    'k8s_persistent_volume_claim',
    'k8s_pod',
    'k8s_replica_set',
    'k8s_replication_controller',
    'k8s_role',
    'k8s_secret',
    'k8s_service_account',
    'k8s_service',
    'k8s_stateful_set',
]


class KubernetesClient(BaseClient):

    def __init__(self, **kwargs):
        self.scope = kwargs.get('metadata', {}).get('scope', 'local')
        self.auth_url = kwargs.get('metadata', {}).get('cluster', {}).get('server', 'N/A')
        super(KubernetesClient, self).__init__(**kwargs)

    def auth(self):
        status = True
        try:
            config_file, filename = tempfile.mkstemp()
            config_content = {
                'apiVersion': 'v1',
                'clusters': [{
                    'cluster': self.metadata['cluster'],
                    'name': self.name,
                }],
                'contexts': [{
                    'context': {
                        'cluster': self.name,
                        'user': self.name,
                    },
                    'name': self.name,
                }],
                'current-context': self.name,
                'kind': 'Config',
                'preferences': {},
                'users': [{
                    'name': self.name,
                    'user': self.metadata['user']
                }]
            }
            os.write(config_file, pyaml.dump(config_content).encode())
            os.close(config_file)
            self.config_wrapper = pykube.KubeConfig.from_file(filename)
            os.remove(filename)
            self.api = pykube.HTTPClient(self.config_wrapper)
            pods = pykube.Pod.objects(self.api).filter(namespace="kube-system")
            for pod in pods:
                pass

        except URLError as exception:
            logger.error(exception)
            status = False
        except ConnectionError as exception:
            logger.error(exception)
            status = False

        return status

    def get_kubeconfig(self):
            config_content = {
                'apiVersion': 'v1',
                'clusters': [{
                    'cluster': self.metadata['cluster'],
                    'name': self.name,
                }],
                'contexts': [{
                    'context': {
                        'cluster': self.name,
                        'user': self.name,
                    },
                    'name': self.name,
                }],
                'current-context': self.name,
                'kind': 'Config',
                'preferences': {},
                'users': [{
                    'name': self.name,
                    'user': self.metadata['user']
                }]
            }
            return pyaml.dump(config_content)

    def update_resources(self, resources=None):
        if self.auth():
            if resources is None:
                resources = DEFAULT_RESOURCES
                if self.scope == 'global':
                    resources += ['k8s_namespace', 'k8s_node']

            for resource in resources:
                metadata = self.get_resource_metadata(resource)
                self.process_resource_metadata(resource, metadata)
                count = len(self.resources.get(resource, {}))
                logger.info("Processed {} {} resources".format(count,
                                                               resource))
            self.process_relation_metadata()

    def get_resource_status(self, kind, metadata):
        phase = metadata.get('status', {}).get('phase', '')
        if kind == 'k8s_pod':
            if phase == 'Running':
                return 'active'
        elif kind == 'k8s_namespace':
            if phase == 'Active':
                return 'active'
        return 'unknown'

    def process_resource_metadata(self, kind, metadata):
        if kind == 'k8s_cluster':
            for cluster in metadata:
                self._create_resource(cluster['uid'],
                                      cluster['name'],
                                      kind,
                                      metadata={})
        elif kind == 'k8s_container':
            for container_id, container in metadata.items():
                self._create_resource(container_id,
                                      container['name'],
                                      kind,
                                      metadata=container)
        else:
            try:
                for item in metadata:
                    resource = item.obj
                    self._create_resource(resource['metadata']['uid'],
                                          resource['metadata']['name'],
                                          kind,
                                          metadata=resource)
            except HTTPError as exception:
                logger.error(exception)
            except ConnectionError as exception:
                logger.error(exception)

    def get_resource_metadata(self, kind):
        logger.info("Getting {} resources".format(kind))
        response = []
        if kind == 'k8s_cluster':
            response.append({
                'name': 'cluster',
                'uid': 'cluster'
            })
        elif kind == 'k8s_config_map':
            response = pykube.ConfigMap.objects(self.api)
        elif kind == 'k8s_container':
            response = {}
            for pod_id, pod in self.resources.get('k8s_pod', {}).items():
                for container in pod['metadata']['spec']['containers']:
                    container_id = "{}-{}".format(pod_id,
                                                  container['name'])
                    response[container_id] = container
                    response[container_id]['pod'] = pod_id
        elif kind == 'k8s_cron_job':
            response = pykube.CronJob.objects(self.api)
        elif kind == 'k8s_daemon_set':
            response = pykube.DaemonSet.objects(self.api)
        elif kind == 'k8s_deployment':
            namespaces = pykube.Namespace.objects(self.api)
            for namespace in namespaces:
                deploys = pykube.Deployment.objects(self.api, namespace.obj['metadata']['name'])
                for deploy in deploys:
                    response.append(deploy)
        elif kind == 'k8s_endpoint':
            response = pykube.Endpoint.objects(self.api)
        elif kind == 'k8s_event':
            response = pykube.Event.objects(self.api)
        elif kind == 'k8s_horizontal_pod_autoscaler':
            response = pykube.HorizontalPodAutoscaler.objects(self.api)
        elif kind == 'k8s_ingress':
            response = pykube.Ingress.objects(self.api)
        elif kind == 'k8s_job':
            response = pykube.Job.objects(self.api)
        elif kind == 'k8s_namespace':
            response = pykube.Namespace.objects(self.api)
        elif kind == 'k8s_node':
            response = pykube.Node.objects(self.api)
        elif kind == 'k8s_persistent_volume':
            response = pykube.PersistentVolume.objects(self.api)
        elif kind == 'k8s_persistent_volume_claim':
            response = pykube.PersistentVolumeClaim.objects(self.api)
        elif kind == 'k8s_pod':
            namespaces = pykube.Namespace.objects(self.api)
            for namespace in namespaces:
                pods = pykube.Pod.objects(self.api, namespace.obj['metadata']['name'])
                for pod in pods:
                    response.append(pod)
        elif kind == 'k8s_replica_set':
            namespaces = pykube.Namespace.objects(self.api)
            for namespace in namespaces:
                rss = pykube.ReplicaSet.objects(self.api, namespace.obj['metadata']['name'])
                for rs in rss:
                    response.append(rs)
        elif kind == 'k8s_replication_controller':
            response = pykube.ReplicationController.objects(self.api)
        elif kind == 'k8s_role':
            response = pykube.Role.objects(self.api)
        elif kind == 'k8s_secret':
            response = pykube.Secret.objects(self.api)
        elif kind == 'k8s_service_account':
            response = pykube.ServiceAccount.objects(self.api)
        elif kind == 'k8s_service':
            namespaces = pykube.Namespace.objects(self.api)
            for namespace in namespaces:
                svcs = pykube.Service.objects(self.api, namespace.obj['metadata']['name'])
                for svc in svcs:
                    response.append(svc)
        elif kind == 'k8s_stateful_set':
            response = pykube.StatefulSet.objects(self.api)
        return response

    def process_relation_metadata(self):
        namespace_2_uid = {}
        for resource_id, resource in self.resources.get('k8s_namespace',
                                                        {}).items():
            resource_mapping = resource['metadata']['metadata']['name']
            namespace_2_uid[resource_mapping] = resource_id
            self._create_relation(
                'contains_k8s_namespace',
                'cluster',
                resource_id)

        node_2_uid = {}
        for resource_id, resource in self.resources.get('k8s_node',
                                                        {}).items():
            resource_mapping = resource['metadata']['metadata']['name']
            node_2_uid[resource_mapping] = resource_id
            self._create_relation(
                'contains_k8s_node',
                'cluster',
                resource_id)

        secret_2_uid = {}
        for resource_id, resource in self.resources.get('k8s_secret',
                                                        {}).items():
            resource_mapping = resource['metadata']['metadata']['name']
            secret_2_uid[resource_mapping] = resource_id

        volume_2_uid = {}
        for resource_id, resource in self.resources.get('k8s_persistent_volume',
                                                        {}).items():
            resource_mapping = resource['metadata']['metadata']['name']
            volume_2_uid[resource_mapping] = resource_id

        service_run_2_uid = {}
        service_app_2_uid = {}
        for resource_id, resource in self.resources.get('k8s_service',
                                                        {}).items():
            if resource['metadata']['spec'].get('selector', {}) is not None:
                if resource['metadata']['spec'].get('selector',
                                                    {}).get('run', False):
                    selector = resource['metadata']['spec']['selector']['run']
                    service_run_2_uid[selector] = resource_id
                if resource['metadata']['spec'].get('selector',
                                                    {}).get('app', False):
                    selector = resource['metadata']['spec']['selector']['app']
                    service_app_2_uid[selector] = resource_id

        # Define relationships between namespace and all namespaced resources.
        for resource_type, resource_dict in self.resources.items():
            for resource_id, resource in resource_dict.items():
                if 'namespace' in resource.get('metadata',
                                               {}).get('metadata', {}):
                    self._create_relation(
                        'in_k8s_namespace',
                        resource_id,
                        namespace_2_uid[resource.get('metadata',
                                                     {}).get('metadata',
                                                             {})['namespace']])

        # Define relationships between service accounts and secrets
        for resource_id, resource in self.resources.get('k8s_service_account',
                                                        {}).items():
            for secret in resource['metadata']['secrets']:
                self._create_relation('use_k8s_secret',
                                      resource_id,
                                      secret_2_uid[secret['name']])
#        for resource_id, resource in self.resources['k8s_persistent_volume'].items():
#            self._create_relation('k8s_persistent_volume-k8s_persistent_volume_claim',
#                                  resource_id,
#                                  volume_2_uid[resource['spec']['volumeName']])

        # Define relationships between replica sets and deployments
        for resource_id, resource in self.resources.get('k8s_replica_set', {}).items():
            deployment_id = resource['metadata']['metadata']['ownerReferences'][0]['uid']
            self._create_relation(
                'in_k8s_deployment',
                resource_id,
                deployment_id)

        for resource_id, resource in self.resources.get('k8s_pod', {}).items():
            # Define relationships between pods and nodes
            if resource['metadata']['spec']['nodeName'] is not None:
                node = resource['metadata']['spec']['nodeName']
                self._create_relation('on_k8s_node',
                                      resource_id,
                                      node_2_uid[node])

            # Define relationships between pods and replication sets and
            # replication controllers.
            if resource['metadata']['metadata'].get('ownerReferences', False):
                if resource['metadata']['metadata']['ownerReferences'][0]['kind'] == 'ReplicaSet':
                    rep_set_id = resource['metadata']['metadata']['ownerReferences'][0]['uid']
                    self._create_relation(
                        'use_k8s_replication',
                        rep_set_id,
                        resource_id)

            # Define relationships between pods and services.
            if resource['metadata']['metadata'].get('labels', {}).get('run', False):
                selector = resource['metadata']['metadata']['labels']['run']
                if selector in service_run_2_uid:
                    self._create_relation(
                        'in_k8s_pod',
                        service_run_2_uid[selector],
                        resource_id)
            if resource['metadata']['metadata'].get('labels', {}).get('app', False):
                try:
                    selector = resource['metadata']['metadata']['labels']['app']
                    self._create_relation(
                        'in_k8s_pod',
                        service_app_2_uid[selector],
                        resource_id)
                except Exception:
                    pass
#                self._create_relation('in_k8s_pod',
#                                      container_id,
#                                      resource_id)

    def get_resource_action_fields(self, resource, action):
        fields = {}
        if resource.kind == 'k8s_service':
            if action == 'discover_service':
                initial_name = '{}-{}-{}'.format(resource.manager.name,
                                                 resource.metadata['metadata']['namespace'],
                                                 resource.metadata['metadata']['name'])
                fields['name'] = forms.CharField(label='Service name',
                                                 help_text='Name of a new resource.',
                                                 initial=initial_name)
                fields['kind'] = forms.ChoiceField(label='Resource type',
                                                   help_text='Kind of resource to be created.',
                                                   choices=(
                                                       ('prometheus', 'Prometheus (monitor)'),
                                                       ('graphite', 'Graphite (monitor)')
                                                   ))
        if resource.kind == 'k8s_cluster':
            if action == 'download_config':
                kubeconfig = self.get_kubeconfig()
                fields['config'] = forms.CharField(label='Config content',
                                                   initial=kubeconfig,
                                                   help_text='The actual KubeConfig to be downloaded',
                                                   widget=forms.Textarea(attrs={'style': 'font-family: monospace;'}))


        return fields


    def process_resource_action(self, resource, action, data):
        if resource.kind == 'k8s_service':
            if action == 'discover_service':
                if data['kind'] == 'prometheus':
                    auth_url = '{}/api/v1/namespaces/{}/services/{}:{}/proxy'.format(resource.manager.metadata['cluster']['server'],
                                                                                     resource.metadata['metadata']['namespace'],
                                                                                     resource.metadata['metadata']['name'],
                                                                                     resource.metadata['spec']['ports'][0]['port'])
                    logger.info(auth_url)
                    ca_cert = base64.b64decode(resource.manager.metadata['cluster']['certificate-authority-data']).decode('utf-8')
                    client_cert = base64.b64decode(resource.manager.metadata['user']['client-certificate-data']).decode('utf-8')
                    client_key = base64.b64decode(resource.manager.metadata['user']['client-key-data']).decode('utf-8')
                    monitor_kwargs = {
                        'name': data['name'],
                        'engine': data['kind'],
                        'metadata': {
                            "auth_url": auth_url,
                            "ca_cert": ca_cert,
                            "client_cert": client_cert,
                            "client_key": client_key,
                        }
                    }
                    monitor = Monitor(**monitor_kwargs)
                    if monitor.client().check_status():
                        monitor.status = 'active'
                    else:
                        monitor.status = 'error'
                    monitor.save()
