
from celery.decorators import task
from celery.utils.log import get_task_logger
from architect.utils import get_module
from architect.manager.models import Manager

log = get_task_logger(__name__)


@task(name="get_manager_status_task")
def get_manager_status_task(manager_name):
    manager = Manager.objects.get(name=manager_name)
    manager_client_class = get_module(manager.engine)
    log.info('Updating manager {}'.format(manager_name))
    manager_client = manager_client_class(**{
        'name': manager_name,
        'engine': manager.engine,
        'metadata': manager.metadata
    })
    manager_client.update_resources()
    manager_client.save()
    return True
