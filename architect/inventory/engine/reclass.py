
from django.conf import settings
from reclass import get_storage
from reclass.core import Core


def inventory(domain='default'):
    '''
    Get inventory nodes from reclass and their associated services and roles.
    '''
    try:
        params = settings.INVENTORY_ENGINES[domain]
    except KeyError:
        raise Exception('No inventory "{}" found.'.format(domain))
    storage = get_storage(params['storage_type'],
                          params['node_dir'],
                          params['class_dir'])
    reclass = Core(storage, None)
    nodes = reclass.inventory()["nodes"]
    return nodes
