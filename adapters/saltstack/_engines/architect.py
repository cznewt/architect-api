# -*- coding: utf-8 -*-
"""
Salt engine for intercepting state jobs and forwarding to the Architect
service.
"""

# Import python libs
from __future__ import absolute_import
import json
import logging

# Import salt libs
import salt.utils.event
import salt.utils.http

log = logging.getLogger(__name__)


def _get_lowstate_resources():
    '''
    Retreive lowstate data of all current Salt resources.
    '''
    kwargs = {
        'timeout': 15,
        'concurrent': True,
        'queue': True
    }
    data = {}

    try:
        lowstate_request = __salt__['saltutil.cmd']('*',
                                                    'state.show_lowstate',
                                                    **kwargs)
    except Exception:
        lowstate_request = {}

    for minion, lowstate_return in lowstate_request.items():
        if lowstate_return.get('retcode') != 0:
            continue
        data[minion] = lowstate_return.get('ret', [])


def start(project='default',
          host='127.0.0.1',
          port=8181,
          username=None,
          password=None):
    '''
    Listen to state jobs events and forward Salt states
    '''
    url = "{}://{}:{}/salt/{}/event/{}".format('http',
                                               host,
                                               port,
                                               'v1',
                                               project)
    target_functions = ['state.sls', 'state.apply', 'state.highstate']

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

    log.info('Salt Architect engine initialised')

    while True:
        event = event_bus.get_event()
        if event and event.get('fun', None) in target_functions:
            is_test_run = 'test=true' in [arg.lower() for arg in event.get('fun_args', [])]
            if not is_test_run:
                data = salt.utils.http.query(url=url,
                                             method='POST',
                                             decode=False,
                                             data=json.dumps(event))
                if 'OK' in data['body']:
                    log.info("Architect Engine request to '{}'"
                             " was successful".format(url))
                else:
                    log.warning("Problem with Architect Engine"
                                " request to '{}' ({})".format(url, data))
