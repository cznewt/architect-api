# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from architect.monitor.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


class ElasticSearchClient(BaseClient):

    def __init__(self, **kwargs):
        super(ElasticSearchClient, self).__init__(**kwargs)

    def check_status(self):
        return False

    def get_range(self):
        data = self.get_http_range_data()
        return self.process_range(data)

    def get_range_url(self):
        url = '/_search'
        return self.base_url + url

    def get_range_params(self):
        return {
            'query': self.queries[0]
        }

    def process_range(self, data):
        np_data = [(series['query'],
                    np.array(series['datapoints'])) for series in data]
        series = [pd.DataFrame(series[:, 0],
                               index=series[:, 1],
                               columns=[query]) for query, series in np_data if series.any()]
        if len(series) > 0:
            return pd.concat(series, axis=1, join='inner')
        else:
            return None
