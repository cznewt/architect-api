
from architect.utils import get_node_icon


def openstack_graph(data):
    resources = {}
    relations = []
    axes = {}
    i = 0
    kinds = 0
    for resource_name, resource_data in data['resources'].items():
        if resource_name != 'os_port':
            kinds += 1

    for resource_name, resource_data in data['resources'].items():
        if resource_name != 'os_port':
            for resource_id, resource_item in resource_data.items():
                resource_item.pop('metadata')
                resources[resource_id] = resource_item
            icon = get_node_icon(data['resource_types'][resource_name]['icon'])
            axes[resource_name] = {
                'x': i,
                'angle': 360 / kinds * i,
                'innerRadius': 0.2,
                'outerRadius': 1.0,
                'name': data['resource_types'][resource_name]['name'],
                'items': len(data['resources'][resource_name]),
                'kind': resource_name,
                'icon': icon,
            }
            i += 1

    for relation_name, relation_data in data['relations'].items():
        for relation in relation_data:
            if relation['source'] in resources and \
               relation['target'] in resources:
                relations.append(relation)

    data['resources'] = resources
    data['relations'] = relations
    data['axes'] = axes
    return data


def default_graph(orig_data):
    data = orig_data.copy()
    resources = {}
    relations = []
    axes = {}
    i = 0
    kinds = 0
    for resource_name, resource_data in data['resources'].items():
        if len(resource_data) > 0:
            kinds += 1

    for resource_name, resource_data in data['resources'].items():
        if len(resource_data) > 0:
            for resource_id, resource_item in resource_data.items():
                resource_item.pop('metadata')
                resources[resource_id] = resource_item
            icon = get_node_icon(data['resource_types'][resource_name]['icon'])
            axes[resource_name] = {
                'x': i,
                'angle': 360 / kinds * i,
                'innerRadius': 0.2,
                'outerRadius': 1.0,
                'name': data['resource_types'][resource_name]['name'],
                'items': len(resource_data),
                'kind': resource_name,
                'icon': icon,
            }
            i += 1

    for relation_name, relation_data in data['relations'].items():
        for relation in relation_data:
            if relation['source'] in resources and \
               relation['target'] in resources:
                relations.append(relation)

    data['resources'] = resources
    data['relations'] = relations
    data['axes'] = axes
    return data


def default_tree(data):
    return data


def transform_data(data, transform='default_graph'):
    if transform == 'openstack_graph':
        return openstack_graph(data)
    if transform == 'default_graph':
        return default_graph(data)
    if transform == 'default_tree':
        return default_tree(data)


def filter_node_types(data, node_types):
    new_resources = {}
    new_axes = {}
    for resource_name, resource in data.get('resources', {}).items():
        if resource['kind'] in node_types:
            new_resources[resource_name] = resource
    data['resources'] = new_resources
    for axe_name, axe in data.get('axes', {}).items():
        if axe_name in node_types:
            new_axes[axe_name] = axe
    data['axes'] = new_axes
    return data


def filter_lone_nodes(data, node_types):
    new_resources = {}
    new_axes = {}
    for resource_name, resource in data.get('resources', {}).items():
        if resource['kind'] in node_types:
            new_resources[resource_name] = resource
    data['resources'] = new_resources
    for axe_name, axe in data.get('axes', {}).items():
        if axe_name in node_types:
            new_axes[axe_name] = axe
    data['axes'] = new_axes
    return data


def clean_relations(data):
    new_relations = []
    for relation in data.get('relations', []):
        if relation['source'] in data['resources'] and \
           relation['target'] in data['resources']:
            new_relations.append(relation)
    data['relations'] = new_relations
    return data

