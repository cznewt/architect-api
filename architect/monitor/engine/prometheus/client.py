# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from datetime import datetime
from architect.monitor.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


class PrometheusClient(BaseClient):

    def __init__(self, **kwargs):
        super(PrometheusClient, self).__init__(**kwargs)

    def check_status(self):
        return False

    def get_series(self):
        data = self.get_http_series_params()
        return self.process_series(data)

    def get_series_params(self):
        return {
            "match[]": '{__name__=~".+"}',
        }

    def get_series_url(self):
        url = '/api/v1/series'
        return self.base_url + url

    def process_series(self, response):
        if response['status'] == 'error':
            self.log_error(response['errorType'], response['error'])
            return {}
        else:
            data = response['data']
            response_data = {}
            for datum in data:
                name = datum.pop('__name__')
                if name not in response_data:
                    response_data[name] = []
                response_data[name].append(datum)
            return response_data

    def get_instant(self):
        data = self.get_http_instant_params()
        return self.process_instant(data)

    def get_instant_params(self):
        return {
            "query": self.queries,
            "time": self.moment
        }

    def get_instant_url(self):
        url = '/api/v1/query'
        return self.base_url + url

    def process_instant(self, response):
        if response['status'] == 'error':
            self.log_error(response['errorType'], response['error'])
        data = response['data']['result']
        for series in data:
            for values in [series['value']]:
                values[0] = pd.Timestamp(datetime.fromtimestamp(values[0]))
                values[1] = float(values[1])
        np_data = [('{}_{}'.format(series['metric']['__name__'],
                                   series['metric']['instance']),
                                   np.array([series['value']])) for series in data]
        series = []
        for query, serie in np_data:
            frame = pd.DataFrame(serie[:, 1],
                                 index=serie[:, 0],
                                 columns=[query])
            series.append(frame)
        if len(series) > 0:
            return pd.concat(series, axis=1, join='inner')
        else:
            return None

    def get_range(self):
        data = self.get_http_range_params()
        return self.process_range(data)

    def get_range_params(self):
        return {
            "query": self.queries,
            "start": self.start,
            "end": self.end,
            "step": self.step
        }

    def get_range_url(self):
        url = '/api/v1/query_range'
        return self.base_url + url

    def process_range(self, response):
        if response['status'] == 'error':
            self.log_error(response['errorType'], response['error'])
        data = response['data']['result']
        for series in data:
            for values in series['values']:
                values[0] = pd.Timestamp(datetime.fromtimestamp(values[0]))
                values[1] = float(values[1])
        np_data = [('{}_{}'.format(series['metric']['__name__'],
                                   series['metric']['instance']),
                                   np.array(series['values'])) for series in data]
        series = []
        for query, serie in np_data:
            frame = pd.DataFrame(serie[:, 1],
                                 index=serie[:, 0],
                                 columns=[query])
            series.append(frame)
        if len(series) > 0:
            return pd.concat(series, axis=1, join='inner')
        else:
            return None
