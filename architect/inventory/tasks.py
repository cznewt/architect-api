
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
    inventory.client().update_resources()
    return True
