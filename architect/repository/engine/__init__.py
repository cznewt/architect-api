# -*- coding: utf-8 -*-

from architect.monitor.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


class PrometheusClient(BaseClient):

    def __init__(self, **kwargs):
        super(PrometheusClient, self).__init__(**kwargs)

    def check_status(self):
        try:
            status = True
        except Exception:
            status = False
        return status

