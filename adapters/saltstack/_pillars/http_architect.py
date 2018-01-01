# -*- coding: utf-8 -*-
"""

A module that adds data to the Pillar structure retrieved by a HTTP request to
the Architect service.

Set the following Salt config to setup an architect service as the external
pillar source:

.. code-block:: yaml

    http_architect: &http_architect
      project: salt.domain
      host: 127.0.0.1
      port: 8181

    ext_pillar:
      - http_architect: *http_architect

If the grains parameter is set, grain keys selected in it's value will be
passed to Architect service in order to populate pillar data based on the
these grain values.

.. code-block:: yaml

    http_architect: &http_architect
      project: salt.domain
      host: 127.0.0.1
      port: 8181
      grains:
      - nodename
      - oscodename

    ext_pillar:
      - http_architect: *http_architect

"""

# Import python libs
from __future__ import absolute_import
import logging

# Import Salt libs
try:
    from salt.ext.six.moves.urllib.parse import quote as _quote
    _HAS_DEPENDENCIES = True
except ImportError:
    _HAS_DEPENDENCIES = False

log = logging.getLogger(__name__)


def __virtual__():
    return _HAS_DEPENDENCIES


def ext_pillar(minion_id,
               pillar,  # pylint: disable=W0613
               project='default',
               host='127.0.0.1',
               port=8181,
               username=None,
               password=None,
               grains=[]):
    """
    Read pillar data from Architect service response.

    :return: A dictionary of the pillar data to add.
    :rtype: dict
    """
    url = "{}://{}:{}/salt/{}/enc/{}/{}/pillar".format('http',
                                                       host,
                                                       port,
                                                       'v1',
                                                       project,
                                                       _quote(minion_id))

    log.info('Getting Pillar data from "{}"'.format(url))
    data = __salt__['http.query'](url=url, decode=True, decode_type='yaml')

    if 'dict' in data:
        return data['dict']

    log.error("Error on minion {}, request sent to {}.".format(minion_id, url))

    for key in data:
        log.error('%s: %s', key, data[key])

    return {}
