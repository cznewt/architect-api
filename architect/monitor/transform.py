
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
            if relation['source'] in resources and relation['target'] in resources:
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
    kinds = len(data['resources'])
    for resource_name, resource_data in data['resources'].items():
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
            if relation['source'] in resources and relation['target'] in resources:
                relations.append(relation)

    data['resources'] = resources
    data['relations'] = relations
    data['axes'] = axes
    return data
