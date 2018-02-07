
from celery.decorators import task
from celery.utils.log import get_task_logger
from architect.utils import get_module
from architect.inventory.models import Inventory

log = get_task_logger(__name__)


@task(name="get_inventory_status_task")
def get_inventory_status_task(inventory_name):
    inventory = Inventory.objects.get(name=inventory_name)
    if inventory.client().check_status():
        inventory.status = 'active'
    else:
        inventory.status = 'error'
    inventory.save()
    return True


@task(name="sync_inventory_resources_task")
def sync_inventory_resources_task(inventory_name):
    inventory = Inventory.objects.get(name=inventory_name)
    inventory_client_class = get_module(inventory.engine, 'inventory')
    log.info('Updating inventory {}'.format(inventory_name))
    inventory_kwargs = {
        'name': inventory_name,
        'engine': inventory.engine,
        'metadata': inventory.metadata
    }
    update_client = inventory_client_class(**inventory_kwargs)
    update_client.update_resources()
    update_client.save()
    cache_client = inventory_client_class(**inventory_kwargs)
    cache_client.refresh_cache()
    return True
