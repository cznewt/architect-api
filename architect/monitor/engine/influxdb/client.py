# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from architect.monitor.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)


class InfluxDbClient(BaseClient):

    def __init__(self, **kwargs):
        super(InfluxDbClient, self).__init__(**kwargs)
        self.partition = kwargs['partition']

    def check_status(self):
        return False

    def get_instant_url(self):
        params = ["q={}".format(query) for query in self.queries]
        if self.user is not None:
            params += ["u={}".format(self.user), "p={}".format(self.password)]
        url = '/query?db={}&epoch=s&{}'.format(self.partition,
                                               '&'.join(params))
        return self.base_url + url

    def get_range(self):
        data = self.get_http_range_params()
        return self.process_range(data)

    def get_range_params(self):
        params = {
            'db': self.partition,
            'epoch': 's',
            'q': self.queries[0]
        }
        if self.user is not None:
            params['u'] = self.user
            params['p'] = self.password
        return params

    def get_range_url(self):
        url = '/query'
        return self.base_url + url

    def process_range(self, response):
        data = response['results'][0]['series']
        np_data = [(series['name'],
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
