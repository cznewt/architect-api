
from django.conf import settings


def inventory(domain='default'):
    '''
    Get inventory nodes from architect and their associated services and roles.
    '''
    try:
        params = settings.INVENTORY_ENGINES[domain]
    except KeyError:
        raise Exception('No inventory "{}" found.'.format(domain))
    nodes = {}
    # TODO: Make this happen
    return nodes
