
import time
from celery.decorators import task
from celery.utils.log import get_task_logger
from architect.utils import get_module
from architect.manager.models import Manager, Resource

logger = get_task_logger(__name__)


@task(name="get_manager_status_task")
def get_manager_status_task(manager_name):
    manager = Manager.objects.get(name=manager_name)
    if manager.client().check_status():
        manager.status = 'active'
    else:
        manager.status = 'error'
    manager.save()
    return True


@task(name="sync_manager_resources_task")
def sync_manager_resources_task(manager_name):
    manager = Manager.objects.get(name=manager_name)
    manager_client_class = get_module(manager.engine, 'manager')
    logger.info('Updating manager {}'.format(manager_name))
    manager_kwargs = {
        'name': manager_name,
        'engine': manager.engine,
        'metadata': manager.metadata
    }
    update_client = manager_client_class(**manager_kwargs)
    update_client.update_resources()
    update_client.save()
    cache_client = manager_client_class(**manager_kwargs)
    cache_client.refresh_cache()
    return True


@task(name="process_resource_action_task")
def process_resource_action_task(manager_name, resource_uid, action, data={}):
    manager = Manager.objects.get(name=manager_name)
    resource = Resource.objects.get(manager=manager,
                                    uid=resource_uid)
    logger.info('Commiting action {} on resource {}'.format(action,
                                                            resource.name))
    manager.client().process_resource_action(resource, action, data)
    return True


@task(name="wait_for_resource_state_task")
def wait_for_resource_state_task(manager_name,
                                 resource_uid,
                                 states=['active', 'error'],
                                 step=10,
                                 timeout=720):
    manager = Manager.objects.get(name=manager_name)
    resource = Resource.objects.get(manager=manager,
                                    uid=resource_uid)
    status = resource.status
    iteration = 0
    logger.info('Started to wait for state(s) {} '
                'on {} {}'.format(', '.join(states),
                                  resource.kind,
                                  resource.name))
    while status not in states:
        if iteration > timeout:
            break
        manager_client = manager.client()
        if manager_client.auth():
            metadata = manager_client.get_resource_metadata(resource.kind,
                                                            resource.uid)
            manager_client.process_resource_metadata(resource.kind, metadata)
            manager_client.save()
            meta = manager_client.resources[resource.kind][resource.uid]['metadata']
            logger.info(meta)
            status = manager_client.get_resource_status(resource.kind, meta)
            logger.info(status)
        iteration += 1
        logger.info('Waiting for state(s) {} '
                    'on resource {}, iteration {}'.format(', '.join(states),
                                                          resource.name,
                                                          iteration))
        time.sleep(step)

    return True
