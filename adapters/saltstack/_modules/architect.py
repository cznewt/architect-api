# -*- coding: utf-8 -*-
'''
Salt modules to work with the Architect service.
'''

# Import python libs
from __future__ import absolute_import
import yaml
import logging
from architect_client.libarchitect import ArchitectClient

__virtualname__ = 'architect'

logger = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def _client():
    return ArchitectClient()


def inventory():
    '''
    Get the Architect metadata inventory

    CLI Examples:

    .. code-block:: bash

        salt-call architect.inventory
    '''
    data = yaml.load(_client().get_data())

    return data


def node_pillar(name):
    '''
    Get the Architect node pillar for given Salt master.

    CLI Examples:

    .. code-block:: bash

        salt-call architect.node_pillar node.domain
    '''

    data = yaml.load(_client().get_data(name))

    return {
        name: data
    }


def node_classify(name, data={}):
    '''
    CLassify node by given dictionary of parameters

    CLI Examples:

    .. code-block:: bash

        salt-call architect.node_classify minion.net {'param1': 'value2'}
    '''
    output = _client().classify_node({
        'name': name,
        'data': data
    })
    return output


def node_info():
    '''
    Get Salt minion metadata and forward it to the Architect master.

    CLI Examples:

    .. code-block:: bash

        salt-call architect.minion_info
    '''
    data = {
        'pillar': __salt__['pillar.data'](),
        'grain': __salt__['grains.items'](),
        'lowstate': __salt__['state.show_lowstate'](),
    }
    return data
