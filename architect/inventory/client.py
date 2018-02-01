
from celery.utils.log import get_logger

logger = get_logger(__name__)


class BaseClient(object):

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.metadata = kwargs.get('metadata', {})
        self.kind = kwargs.get('engine')

    def check_status(self):
        raise NotImplementedError
