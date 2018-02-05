# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from architect.monitor.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


class GraphiteClient(BaseClient):

    def __init__(self, **kwargs):
        super(GraphiteClient, self).__init__(**kwargs)

    def check_status(self):
        return False

    def get_instant_url(self):
        params = ["from={}".format(self.start),
                  "until={}".format(self.end)]
        params += ["target={}".format(query) for query in self.queries]
        url = '/render?format=json&{}'.format('&'.join(params))
        return self.base_url + url

    def get_range(self):
        data = self.get_http_range_params()
        return self.process_range(data)

    def get_range_params(self):
        return {
            'target': self.queries,
            'from': self.start,
            'until': self.end,
            'format': 'json'
        }

    def get_range_url(self):
        url = '/render'
        return self.base_url + url

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
