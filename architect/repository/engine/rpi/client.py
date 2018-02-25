# -*- coding: utf-8 -*-

from architect.repository.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


class RpiClient(BaseClient):

    def __init__(self, **kwargs):
        super(RpiClient, self).__init__(**kwargs)

    def check_status(self):
        return False
