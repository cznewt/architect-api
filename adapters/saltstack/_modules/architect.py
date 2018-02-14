# -*- coding: utf-8 -*-
'''
Salt modules to work with the Architect service.
'''

# Import python libs
from __future__ import absolute_import
import yaml
from architect_client.libarchitect import ArchitectClient
import logging

__virtualname__ = 'architect'

logger = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def _client():
    return ArchitectClient()


def get_inventory():
    '''
    Get the Architect metadata inventory for given Salt master.

    CLI Examples:

    .. code-block:: bash

        salt-call architect.get_inventory
    '''
    data = yaml.load(_client().get_data())

    return data


def get_node(name):
    '''
    Get the Architect node metadata for given Salt master.

    CLI Examples:

    .. code-block:: bash

        salt-call architect.get_node node.domain
    '''

    data = yaml.load(_client().get_data(name))

    return {
        name: data
    }


def collect_minion_info():
    '''
    Get Salt minion metadata and forward it to the Architect master.

    CLI Examples:

    .. code-block:: bash

        salt-call architect.collect_minion_info
    '''

    data = {
        'pillar': __salt__['pillar.data'](),
        'grain': __salt__['grains.items'](),
    }
    output = _client().push_salt_minion({data['grain']['id']: data})
    return output
