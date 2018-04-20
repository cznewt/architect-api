
from celery.decorators import task
from celery.utils.log import get_task_logger
from architect.utils import get_module
from architect.repository.models import Repository

logger = get_task_logger(__name__)


@task(name="generate_image_task")
def generate_image_task(repository_name, image_parameters):
    repository = Repository.objects.get(name=repository_name)
    result = repository.client().generate_image(image_parameters)
    return result
