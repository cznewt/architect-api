# -*- coding: utf-8 -*-
'''
Salt modules to work with the Architect service.
'''

# Import python libs
from __future__ import absolute_import
import logging

__virtualname__ = 'architect'

log = logging.getlogger(__name__)


def __virtual__():
    return __virtualname__


def _get_url(opts):
    '''
    Get the Architect service url from options.
    '''
    return "{}://{}:{}/salt/{}/enc/{}".format('http',
                                              opts.get('host'),
                                              opts.get('port'),
                                              'v1',
                                              opts.get('project'))


def _get_options():
    '''
    Get the Architect service options from Salt config.
    '''
    defaults = {
        'project': 'newt.work',
        'host': '127.0.0.1',
        'port': 8181,
        'username': None,
        'passwd': None
    }
    _options = {}

    for key, default in defaults.items():
        config_key = '{}.{}'.format(__virtualname__, key)
        _options[key] = __salt__['config.get'](config_key, default)

    return _options


def get_inventory():
    '''
    Get the Architect metadata inventory for given Salt master.

    CLI Examples:

    .. code-block:: bash

        salt-call architect.get_inventory
    '''
    options = _get_options()
    url = _get_url(options)
    data = __salt__['http.query'](url=url, decode=True, decode_type='yaml')

    if 'dict' in data:
        return data['dict']

    log.error("Error on query: %s\nMore Info:\n", url)

    for key in data:
        log.error('%s: %s', key, data[key])

    return {}


def get_node(name):
    '''
    Get the Architect node metadata for given Salt master.

    CLI Examples:

    .. code-block:: bash

        salt-call architect.get_node node.domain
    '''
    options = _get_options()
    url = _get_url(options)
    data = __salt__['http.query'](url=url, decode=True, decode_type='yaml')

    if 'dict' in data:
        return {
            name: data['dict'][name]
        }

    log.error("Error on query: %s\nMore Info:\n", url)

    for key in data:
        log.error('%s: %s', key, data[key])

    return {}
