# -*- coding: utf-8 -*-
"""
A module that adds data to the Top file retrieved by a request to Architect
service.

Set the following Salt config to setup an Architect service as the external
Top source:

.. code-block:: yaml

    http_architect: &http_architect
      project: newt.work
      host: 127.0.0.1
      port: 8181

    master_tops:
      http_architect: *http_architect

"""

# Import python libs
from __future__ import absolute_import
import logging

# Import Salt libs
import salt.utils.http
from salt.ext.six.moves.urllib.parse import quote as _quote

__virtualname__ = 'http_architect'

log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def top(**kwargs):
    """
    Read Top file data from Architect service response.

    :return: A list of Top file services.
    :rtype: list
    """
    minion_id = kwargs['opts']['id']
    if 'http_architect' not in kwargs['opts']:
        raise Exception('http_architect configuration is missing.')
    host = kwargs['opts']['http_architect']['host']
    port = kwargs['opts']['http_architect']['port']
    project = kwargs['opts']['http_architect']['project']
    url = "{}://{}:{}/salt/{}/enc/{}/{}/top".format('http',
                                                    host,
                                                    port,
                                                    'v1',
                                                    project,
                                                    _quote(minion_id))

    log.info('Getting Tops data from "{}"'.format(url))
    data = salt.utils.http.query(url=url, decode=True, decode_type='yaml')

    if 'dict' in data:
        return {'base': data['dict']}

    for key in data:
        log.error('%s: %s', key, data[key])

    return {}
