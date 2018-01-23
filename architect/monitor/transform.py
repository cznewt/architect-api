
from architect.utils import get_node_icon


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def default_graph(orig_data, options={}):
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
            resources = merge_dicts(resources, resource_data)
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


def parse_hier_level(resources, relations, resource, layers, level):
    layer = layers[level]
    children = []
    if 'source' in layer:
        allowed_sources = []
        for relation in relations[layer['source']]:
            if relation['source'] == resource.get('id'):
                allowed_sources.append(relation['target'])
    if 'target' in layer:
        allowed_targets = []
        for relation in relations[layer['target']]:
            if relation['target'] == resource.get('id'):
                allowed_targets.append(relation['source'])
    for res_id, res in resources[layer['kind']].items():
        if 'source' in layer:
            if res_id not in allowed_sources:
                continue
        if 'target' in layer:
            if res_id not in allowed_targets:
                continue
        child = {
            'id': res_id,
            'name': res['name'],
            'status': res['status'],
            'kind': layer['kind']
        }
        if level < len(layers) - 1:
            child = parse_hier_level(resources,
                                     relations,
                                     child,
                                     layers,
                                     level + 1)
        else:
            child['size'] = 1
        children.append(child)
    if len(children) > 0:
        resource['children'] = children
    else:
        resource['size'] = 1
    return resource


def default_hier(orig_data, layers):
    data = orig_data.copy()
    root_layer = layers[0]
    if root_layer['kind'] is None:
        root_resource = {
            'id': None,
            'name': root_layer['name'],
            'status': 'unknown',
            'kind': 'root',
        }
    root_resource = parse_hier_level(data['resources'],
                                     data['relations'],
                                     root_resource,
                                     layers,
                                     1)
    data.pop('relations')
    data.pop('relation_types')
    data.pop('resource_types')
    data['resources'] = root_resource
    return data


def transform_data(data, transform='default_graph', options={}):
    if transform == 'default_graph':
        return default_graph(data, options)
    elif transform == 'default_hier':
        return default_hier(data, options)


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
    for relation in data.get('relations', []):
        if relation['source'] in data['resources']:
            data['resources'][relation['source']]['keep'] = True
        if relation['target'] in data['resources']:
            data['resources'][relation['target']]['keep'] = True
    for resource_name, resource in data.get('resources', {}).items():
        if resource['kind'] in node_types:
            if resource.get('keep', False):
                resource.pop('keep')
                new_resources[resource_name] = resource
        else:
            new_resources[resource_name] = resource
    data['resources'] = new_resources
    return data


def clean_relations(data):
    new_relations = []
    for relation in data.get('relations', []):
        if relation['source'] in data['resources'] and \
           relation['target'] in data['resources']:
            new_relations.append(relation)
    data['relations'] = new_relations
    return data
