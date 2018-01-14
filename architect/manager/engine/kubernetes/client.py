# -*- coding: utf-8 -*-

import os
import pyaml
import tempfile
import pykube
from urllib.error import URLError
from requests.exceptions import HTTPError, ConnectionError
from architect.manager.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


class KubernetesClient(BaseClient):

    def __init__(self, **kwargs):
        self.scope = kwargs.get('metadata', {}).get('scope', 'local')
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
        except URLError as exception:
            logger.error(exception)
            status = False
        return status

    def update_resources(self, resources=None):
        if self.auth():
            if resources is None:
                resources = [
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
        return 'unknown'

    def process_resource_metadata(self, kind, metadata):
        if kind == 'k8s_container':
            for container_id, container in metadata.items():
                self._create_resource(container_id,
                                      container['name'],
                                      'k8s_container',
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
        if kind == 'k8s_config_map':
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
            response = pykube.Deployment.objects(self.api)
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
            response = pykube.Pod.objects(self.api)
        elif kind == 'k8s_replica_set':
            response = pykube.ReplicaSet.objects(self.api)
        elif kind == 'k8s_replication_controller':
            response = pykube.ReplicationController.objects(self.api)
        elif kind == 'k8s_role':
            response = pykube.Role.objects(self.api)
        elif kind == 'k8s_secret':
            response = pykube.Secret.objects(self.api)
        elif kind == 'k8s_service_account':
            response = pykube.ServiceAccount.objects(self.api)
        elif kind == 'k8s_service':
            response = pykube.Service.objects(self.api)
        elif kind == 'k8s_stateful_set':
            response = pykube.StatefulSet.objects(self.api)
        return response

    def process_relation_metadata(self):
        namespace_2_uid = {}
        for resource_id, resource in self.resources.get('k8s_namespace',
                                                        {}).items():
            resource_mapping = resource['metadata']['metadata']['name']
            namespace_2_uid[resource_mapping] = resource_id

        node_2_uid = {}
        for resource_id, resource in self.resources.get('k8s_node',
                                                        {}).items():
            resource_mapping = resource['metadata']['metadata']['name']
            node_2_uid[resource_mapping] = resource_id

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
            if resource['metadata']['metadata']['labels'].get('run', False):
                selector = resource['metadata']['metadata']['labels']['run']
                self._create_relation(
                    'in_k8s_pod',
                    service_run_2_uid[selector],
                    resource_id)
            if resource['metadata']['metadata']['labels'].get('app', False):
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
