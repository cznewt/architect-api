# -*- coding: utf-8 -*-

import io
import python_terraform
from pydot import graph_from_dot_data
from architect.manager.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)

relation_mapping = {
    'tf_openstack_compute_instance_v2-tf_openstack_compute_keypair_v2': 'using_tf_key_pair',
    'tf_openstack_networking_subnet_v2-tf_openstack_networking_network_v2': 'in_tf_net',
    'tf_openstack_compute_floatingip_associate_v2-tf_openstack_networking_floatingip_v2': 'links_tf_floating_ip',
    'tf_openstack_networking_floatingip_v2-tf_openstack_networking_router_interface_v2': 'links_tf_floating_ip',
    'tf_openstack_networking_router_interface_v2-tf_openstack_networking_subnet_v2': 'in_tf_subnet',
    'tf_openstack_networking_router_interface_v2-tf_openstack_networking_router_v2': 'links_tf_router',
    'tf_openstack_compute_instance_v2-tf_openstack_networking_network_v2': 'in_tf_net',
    'tf_openstack_compute_floatingip_associate_v2-tf_openstack_compute_instance_v2': 'links_tf_floating_instance',
    'tf_openstack_compute_instance_v2-tf_openstack_compute_secgroup_v2': 'has_tf_security_group',
}


class TerraformClient(BaseClient):

    def __init__(self, **kwargs):
        super(TerraformClient, self).__init__(**kwargs)
        self.client = python_terraform.Terraform(
            working_dir=self.config['dir'])

    def _clean_name(self, name):
        return name.replace('"', '').replace('[root] ', '').strip()

    def update_resources(self, resources=None):
        self.process_resource_metadata()
        self.process_relation_metadata()

    def get_resource_status(self, kind, metadata):
        return 'unknown'

    def process_resource_metadata(self):
        return_code, raw_data, stderr = self.client.graph(
            no_color=python_terraform.IsFlagged)
        graph = graph_from_dot_data(raw_data)[0]
        nodes = {}
        for node in graph.obj_dict['subgraphs']['"root"'][0]['nodes']:
            clean_node = 'tf_{}'.format(self._clean_name(node).split('.')[0])
            if clean_node in self._schema['resource']:
                nodes[self._clean_name(node)] = {
                    'id': self._clean_name(node),
                    'name': self._clean_name(node).split('.')[1],
                    'kind': 'tf_{}'.format(self._clean_name(node).split('.')[0]),
                    'metadata': {}
                }
        res = None
        return_code, raw_data, stderr = self.client.show(
            no_color=python_terraform.IsFlagged)
        raw_data = raw_data.split('Outputs:')[0]
        data_buffer = io.StringIO(raw_data)
        for line in data_buffer.readlines():
            if line.strip() == '':
                pass
            elif line.startswith('  '):
                meta_key, meta_value = line.split(' = ')
                res['metadata'][meta_key.strip()] = meta_value.strip()
            else:
                if res is not None:
                    nodes[res['id']]['metadata'] = res['metadata']
                resource_id = line.replace(' (tainted', '') \
                    .replace(':', '').replace('(', '').replace(')', '').strip()
                try:
                    resource_kind, resource_name = str(resource_id).split('.')
                    res = {
                        'id': resource_id,
                        'name': resource_name.strip(),
                        'kind': 'tf_{}'.format(resource_kind),
                        'metadata': {}
                    }
                except Exception as exception:
                    logger.error(exception)
        for node_name, node in nodes.items():
            self._create_resource(node['id'], node['name'],
                                  node['kind'], None,
                                  metadata=node['metadata'])

    def process_relation_metadata(self):
        return_code, raw_data, stderr = self.client.graph(
            no_color=python_terraform.IsFlagged)
        graph = graph_from_dot_data(raw_data)[0]
        for edge in graph.obj_dict['subgraphs']['"root"'][0]['edges']:
            source = self._clean_name(edge[0]).split('.')
            target = self._clean_name(edge[1]).split('.')
            if 'tf_{}'.format(source[0]) in self.resources and 'tf_{}'.format(target[0]) in self.resources:
                self._create_relation(
                    relation_mapping['tf_{}-tf_{}'.format(source[0], target[0])],
                    '{}.{}'.format(source[0], source[1]),
                    '{}.{}'.format(target[0], target[1]))
