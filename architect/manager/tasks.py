
from celery.decorators import task
from celery.utils.log import get_task_logger
from architect.utils import get_module
from architect.manager.models import Manager

log = get_task_logger(__name__)


@task(name="get_manager_status_task")
def get_manager_status_task(manager_name):
    manager = Manager.objects.get(name=manager_name)
    manager_client_class = get_module(manager.engine, 'manager')
    log.info('Updating manager {}'.format(manager_name))
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
