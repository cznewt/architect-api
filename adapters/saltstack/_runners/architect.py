
# Import python libs
import logging
import json

# Import salt modules
import salt.client

__virtualname__ = 'architect'

log = logging.getLogger(__name__)


def _process_resource(local_target, local_function, api_resource):
    client = salt.client.LocalClient(__opts__['conf_file'])
    result = client.cmd(local_target, local_function, timeout=1)
    host = __opts__['http_architect']['host']
    port = __opts__['http_architect']['port']
    project = __opts__['http_architect']['project']
    url = "{}://{}:{}/salt/{}/{}/{}".format('http',
                                            host,
                                            port,
                                            'v1',
                                            api_resource,
                                            project)
    data = salt.utils.http.query(url=url,
                                 method='POST',
                                 decode=False,
                                 data=json.dumps(result))
    return data


def sync_grain(target):
    """
    Synchronise grain data for target minion(s).

    CLI Example:

    .. code-block:: bash

        salt-run architect.sync_grain '*'
    """
    data = _process_resource(target, 'grains.items', 'grain')
    if 'body' in data and 'OK' in data['body']:
        log.info("Architect Runner grain request was successful")
        return True
    else:
        log.warning("Problem with Architect Runner grain request")
        return False


def sync_lowstate(target):
    """
    Synchronise lowstate data for target minion(s).

    CLI Example:

    .. code-block:: bash

        salt-run architect.sync_lowstate '*'
    """
    data = _process_resource(target, 'state.show_lowstate', 'lowstate')
    if 'body' in data and 'OK' in data['body']:
        log.info("Architect Runner lowstate request was successful")
        return True
    else:
        log.warning("Problem with Architect Runner lowstate request")
        return False


def sync_pillar(target):
    """
    Synchronise pillar data for target minion(s).

    CLI Example:

    .. code-block:: bash

        salt-run architect.sync_pillar '*'
    """
    data = _process_resource(target, 'pillar.data', 'pillar')
    if 'body' in data and 'OK' in data['body']:
        log.info("Architect Runner pillar request was successful")
        return True
    else:
        log.warning("Problem with Architect Runner pillar request")
        return False


def sync_all(target):
    """
    Synchronise all available data for target minion(s).

    CLI Example:

    .. code-block:: bash

        salt-run architect.sync_all '*'
    """
    sync_grain(target)
    sync_pillar(target)
    sync_lowstate(target)
