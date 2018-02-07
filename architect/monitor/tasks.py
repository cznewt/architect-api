
from celery.decorators import task
from celery.utils.log import get_task_logger
from architect.monitor.models import Monitor

log = get_task_logger(__name__)


@task(name="get_monitor_status_task")
def get_monitor_status_task(monitor_name):
    monitor = Monitor.objects.get(name=monitor_name)
    if monitor.client().check_status():
        monitor.status = 'active'
    else:
        monitor.status = 'error'
    monitor.save()
    return True


@task(name="sync_monitor_resources_task")
def sync_monitor_resources_task(monitor_name):
    monitor = Monitor.objects.get(name=monitor_name)
    log.info('Updating monitor {}'.format(monitor_name))
    client = monitor.client()
    client.update_resources()
    client.save()
    return True
