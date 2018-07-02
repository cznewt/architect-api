# -*- coding: utf-8 -*-

import io
import json
import yaml
import os
import glob
import datetime
import petname
from django import forms
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

DEFAULT_RESOURCES = [
    'tf_template',
    'tf_state',
#    'tf_resource',
]

class TerraformClient(BaseClient):

    def __init__(self, **kwargs):
        super(TerraformClient, self).__init__(**kwargs)

    def auth(self):
        return True

    def check_status(self):
        if os.path.isdir(self.metadata['template_path']):
            return True
        else:
            return False

    def _clean_name(self, name):
        return name.replace('"', '').replace('[root] ', '').strip()

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
        if not isinstance(metadata, dict):
            return 'unknown'
        if kind == 'tf_template':
            if metadata.get('status', None) == True:
                return 'active'
            if metadata.get('status', None) == False:
                return 'error'
        elif kind == 'tf_state':
            if metadata.get('states', [{'state': None}])[0].get('state', None) is None:
                return 'build'
            return 'active'
        return 'unknown'

    def get_resource_metadata(self, kind, uid=None):
        logger.info("Getting {} resources".format(kind))
        response = {}
        if kind == 'tf_template':
            path = self.metadata['template_path']
            if uid is None:
                templates = glob.glob('{}/*'.format(path))
            else:
                templates = ['{}/{}'.format(path, uid)]
            for template in templates:
                resource = []
                variable = []
                files = glob.glob('{}/*.tf'.format(template))
                for filename in files:
                    with open(filename) as file_handler:
                        name = filename.replace('{}/'.format(template), '')
                        resource.append({
                            'name': name,
                            'items': file_handler.read(),
                            'format': 'hcl'
                        })
                files = glob.glob('{}/*.tf.json'.format(template))
                for filename in files:
                    with open(filename) as file_handler:
                        name = filename.replace('{}/'.format(template), '')
                        resource.append({
                            'name': name,
                            'items': json.loads(file_handler.read()),
                            'format': 'json'
                        })
                files = glob.glob('{}/*.tfvars'.format(template))
                for filename in files:
                    with open(filename) as file_handler:
                        name = filename.replace('{}/'.format(template), '')
                        variable.append({
                            'name': name,
                            'items': file_handler.read(),
                            'format': 'hcl'
                        })
                files = glob.glob('{}/*.tfvars.json'.format(template))
                for filename in files:
                    with open(filename) as file_handler:
                        name = filename.replace('{}/'.format(template), '')
                        variable.append({
                            'name': name,
                            'items': json.loads(file_handler.read()),
                            'format': 'json'
                        })
                client = python_terraform.Terraform(
                    working_dir=template)
                return_code, raw_data, stderr = client.init(
                    reconfigure=python_terraform.IsFlagged,
                    backend=False)
                if stderr == '':
                    status = True
                    init = raw_data
                else:
                    status = False
                    init = stderr
                data = {
                    'init': raw_data,
                    'status': status,
                    'resources': resource,
                    'variables': variable
                }
                response[template.replace('{}/'.format(path), '')] = data
        elif kind == 'tf_state':
            path = self.metadata['template_path']
            if uid is None:
                templates = glob.glob('{}/*'.format(path))
            else:
                templates = ['{}/{}'.format(path, uid)]
            for template in templates:
                state = {}
                if os.path.isfile('{}/terraform.tfstate'.format(template)):
                    with open('{}/terraform.tfstate'.format(template)) as file_handler:
                        state['default'] = file_handler.read()
                files = glob.glob('{}/terraform.tfstate.d/*/terraform.tfstate'.format(template))
                for filename in files:
                    with open(filename) as file_handler:
                        name = filename.replace('{}/terraform.tfstate.d/'.format(template), '').replace('/terraform.tfstate', '')
                        state[name] = file_handler.read()
                for name, content in state.items():
                    data = {
                        'state': json.loads(content),
                        'template': template.replace('{}/'.format(path), '')
                    }
                    response[name] = data
        elif kind == 'tf_resource':
            return_code, raw_data, stderr = self.client.graph(
                no_color=python_terraform.IsFlagged)
            graph = graph_from_dot_data(raw_data)[0]
            #response = graph.obj_dict['subgraphs']['"root"'][0]['nodes']
        return response

    def process_resource_metadata(self, kind, metadata):
        if kind == 'tf_template':
            for resource_name, resource in metadata.items():
                self._create_resource(resource_name,
                                      resource_name,
                                      'tf_template',
                                      metadata=resource)
        elif kind == 'tf_state':
            resources = self.get_resources('tf_state')
            for resource_name, resource in metadata.items():
                if resource_name in resources:
                    current_states = resources[resource_name]['metadata']['states']
                    if current_states[-1]['serial'] != resource['state']['serial']:
                        states = current_states.append(resource['state'])
                    else:
                        states = current_states
                    self._create_resource(resource_name,
                                          resource_name,
                                          'tf_state',
                                          metadata={
                                              'states': states,
                                              'template': resource['template']
                                          })
                else:
                    self._create_resource(resource_name,
                                          resource_name,
                                          'tf_state',
                                          metadata={
                                              'states': [resource['state']],
                                              'template': resource['template']
                                          })
        elif kind == 'tf_resource':
            nodes = {}
            for node in metadata:
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
        for resource_id, resource in self.resources.get('tf_state',
                                                        {}).items():
            self._create_relation(
                'uses_tf_template',
                resource_id,
                resource['metadata']['template'])
        """
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
        """

    def get_resource_action_fields(self, resource, action):
        fields = {}
        if resource.kind == 'tf_template':
            if action == 'create':
                initial_name = '{}-{}'.format(resource.name.replace('_', '-'),
                                              self.generate_name())
                initial_variables = yaml.safe_dump(resource.metadata['variables'][0]['items'],
                                                   default_flow_style=False)
                fields['name'] = forms.CharField(label='Template name',
                                                 initial=initial_name)
                fields['variables'] = forms.CharField(label='Variables',
                                                      widget=forms.Textarea,
                                                      initial=initial_variables,
                                                      help_text="Use YAML/JSON syntax.")
        return fields

    def process_resource_action(self, resource, action, data):
        if resource.kind == 'tf_template':
            if action == 'create':
                metadata = {
                    'name': data['name'],
                    'template_dir': '{}/{}'.format(self.metadata['template_path'],
                                                   resource.name),
                    'states': [{
                        'variables': yaml.safe_load(data['variables']),
                        'state': None,
                        'min_serial': 1,
                        'timestamp': datetime.datetime.now()
                    }],
                }
                self._create_resource(data['name'],
                                      data['name'],
                                      'tf_state',
                                      metadata=metadata)
                self._create_relation(
                    'uses_tf_template',
                    data['name'],
                    resource.uid)
                self.save()
                self.create_resource('tf_state', metadata)

    def generate_name(self, separator='-', word_count=2):
        return petname.Generate(int(word_count), separator)

    def create_resource(self, kind, metadata):
        logger.info("Creating {} resource".format(kind))

        if kind == 'tf_state':
            state_dir = "terraform.tfstate.d/{}".format(metadata['name'])
            os.makedirs(os.path.join(metadata['template_dir'], state_dir))
            with open(os.path.join(metadata['template_dir'], '.terraform', 'environment'), 'w') as file_handler:
                file_handler.write(metadata['name'])
            self.client = python_terraform.Terraform(
                working_dir=metadata['template_dir'],
                state="{}/terraform.tfstate".format(state_dir))
            return_code, raw_data, stderr = self.client.apply(
                no_color=python_terraform.IsFlagged,
                auto_approve=True,
                var=metadata['states'][0]['variables'])
            if os.path.isfile('{}/terraform.tfstate'.format(os.path.join(metadata['template_dir'], state_dir))):
                with open('{}/terraform.tfstate'.format(os.path.join(metadata['template_dir'], state_dir))) as file_handler:
                    metadata['states'][0]['state'] = json.loads(file_handler.read())
                    metadata['states'][0]['serial'] = metadata['states'][0]['state']['serial']
                    metadata['states'][0].pop('min_serial')
            return_code, raw_data, stderr = self.client.cmd('output',
                json=python_terraform.IsFlagged)
            if return_code == 0:
                metadata['states'][0]['output'] = json.loads(raw_data)
            self._create_resource(metadata['name'],
                                  metadata['name'],
                                  'tf_state',
                                  metadata=metadata)
            self.save()
