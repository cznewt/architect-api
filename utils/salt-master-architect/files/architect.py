# -*- coding: utf-8 -*-
"""
Salt engine for intercepting state jobs and forwarding to the Architect.
"""

# Import python libs
from __future__ import absolute_import
import logging
from architect_client.libarchitect import ArchitectClient

# Import salt libs
import salt.utils.event

logger = logging.getLogger(__name__)


def start():
    '''
    Listen to state jobs events and forward state functions and node info
    '''
    state_functions = ['state.sls', 'state.apply', 'state.highstate']
    model_functions = ['architect.node_info']
    class_tag = 'architect/minion/classify'

    if __opts__['__role'] == 'master':
        event_bus = salt.utils.event.get_master_event(__opts__,
                                                      __opts__['sock_dir'],
                                                      listen=True)
    else:
        event_bus = salt.utils.event.get_event(
            'minion',
            transport=__opts__['transport'],
            opts=__opts__,
            sock_dir=__opts__['sock_dir'],
            listen=True)

    logger.info('Architect Engine initialised')

    while True:
        event = event_bus.get_event()
        if event and event.get('fun', None) in state_functions:
            is_test_run = 'test=true' in [arg.lower()
                                          for arg in event.get('fun_args', [])]
            if not is_test_run:
                output = ArchitectClient().push_event(event)
                logger.info("Sent Architect state function {}".format(output))
        if event and event.get('fun', None) in model_functions:
            output = ArchitectClient().push_node_info(
                {event['id']: event['return']})
            logger.info("Sent Architect node info function {}".format(output))
        if event and event.get('tag', None) == class_tag:
            output = ArchitectClient().classify_node({
                'name': event['id'],
                'data': event['data']
            })
            logger.info("Sent Architect node classification {}".format(output))
