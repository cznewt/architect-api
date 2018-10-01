# -*- coding: utf-8 -*-

import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from architect.monitor.client import BaseClient
from celery.utils.log import get_logger

logger = get_logger(__name__)

DEFAULT_RESOURCES = [
    'prom_job',
    'prom_target',
    'prom_metric',
#    'prom_record',
#    'prom_alarm',
]

class PrometheusClient(BaseClient):

    def __init__(self, **kwargs):
        super(PrometheusClient, self).__init__(**kwargs)

    def check_status(self):
        status = True
        logger.info('Checking status of monitor {} at {}'.format(self.name, self.base_url))
        try:
            requests.get(self.base_url,
                     cert=self.cert,
                     verify=self.verify)
        except requests.exceptions.ConnectionError as err:
            logger.error(err)
            status = False
        return status

    def get_resource_status(self, kind, metadata):
        if kind == 'prom_target':
            if metadata['health'] != 'up':
                return 'error'
        return 'active'

    def update_resources(self, resources=None):
        series = self.get_series()
        series_metadata, series_status = self.get_series_metadata()
        targets_metadata, targets_status = self.get_targets_metadata()
        jobs = {}
        targets = {}
        metrics = {}
        if targets_status:
            for targets_metadatum in targets_metadata:
                targets[targets_metadatum['scrapeUrl']] = targets_metadatum
                if targets_metadatum['labels']['job'] not in jobs:
                    jobs[targets_metadatum['labels']['job']] = {}
        if series_status:
            for series_metadatum in series_metadata:
                if not series_metadatum['metric'] in metrics:
                    metrics[series_metadatum['metric']] = {
                        'type': series_metadatum['type'],
                        'help': series_metadatum['help']
                    }

        for job_name, job in jobs.items():
            self._create_resource(job_name,
                                  job_name,
                                  'prom_job',
                                  metadata=job)

        metric_label_map = {}

        target_label_map = {}

        for target_name, target in targets.items():
            self._create_resource(target['scrapeUrl'],
                                  target['scrapeUrl'],
                                  'prom_target',
                                  metadata=target)
            self._create_relation(
                'by_job',
                target['scrapeUrl'],
                target['labels']['job'])

            for label_name, label_value in target.get('labels', {}).items():
                selector = '{}: {}'.format(label_name, label_value)
                if selector not in target_label_map:
                    target_label_map[selector] = []
                target_label_map[selector].append(target['scrapeUrl'])

        for target_name, target in target_label_map.items():
            logger.info(target_name)
            logger.info(target)

        i = 0

        for series_name, series_item in series.items():
#            logger.info(series_item)
            if series_name in metrics:
                series_item['meta'] = metrics[series_name]
            self._create_resource(series_name,
                                series_name,
                                'prom_metric',
                                metadata=series_item)
            for target in series_item['targets']:
                first_list = True
                uid_list = []
                for label_name, label_value in target.items():
                    #if label_name in ['instance', 'job', 'domain']:
                    label = '{}: {}'.format(label_name, label_value)
                    if label in target_label_map:
                        if first_list:
                            uid_list = target_label_map[label]
                            first_list = False
                        else:
                            uid_list = list(set(uid_list) & set(target_label_map[label]))
                if len(uid_list) == 0:
                    i += 1
                    logger.error('[{}] No targets found for labels {}, metric {}'.format(i, target, series_name))
                elif len(uid_list) > 1:
                    i += 1
                    logger.error('[{}] Multiple targets {} found for labels {}, metric {}'.format(i, uid_list, target, series_name))
                else:
                    for uid in uid_list:
#                        logger.info('Target {} found for labels {}, metric {}'.format(uid_list[0], target, series_name))
                        self._create_relation(
                            'metric_value',
                            series_name,
                            uid)
        if resources is None:
            resources = DEFAULT_RESOURCES
        for resource in resources:
            count = len(self.resources.get(resource, {}))
            logger.info("Processed {} {} resources".format(count,
                                                            resource))
 #           self.process_relation_metadata()

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

    def get_series_metadata(self):
        status = True
        data = json.loads(requests.get(self.get_series_metadata_url(),
                                       params=self.get_series_metadata_params(),
                                       cert=self.cert,
                                       verify=self.verify).text)
        if data.get('status', 'failure') != 'success':
            status = False
        return data.get('data', []), status

    def get_series_metadata_params(self):
        return {
            "match_target": '{job=~".+"}',
        }

    def get_series_metadata_url(self):
        url = '/api/v1/targets/metadata'
        return self.base_url + url


    def delete_series_by_name(self, name):
        data = json.loads(requests.get(self.delete_series_url(),
                                       params=self.delete_series_params(name),
                                       cert=self.cert,
                                       verify=self.verify).text)
        if data.get('status', 'failure') != 'success':
            status = False
        return data.get('data', []), status

    def delete_series_params(self, name):
        return {
            "matchers": [{
                "type": "EQ",
                "name": "__name__",
                "value": name
            }]
        }

    def delete_series_url(self):
        url = '/api/v2/admin/tsdb/delete_series'
        return self.base_url + url

    def get_targets_metadata(self):
        status = True
        data = json.loads(requests.get(self.get_targets_metadata_url(),
                                       cert=self.cert,
                                       verify=self.verify).text)
        if data.get('status', 'failure') != 'success':
            status = False
        return data.get('data', {}).get('activeTargets', []), status

    def get_targets_metadata_url(self):
        url = '/api/v1/targets'
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
                    response_data[name] = {'targets': []}
                response_data[name]['targets'].append(datum)
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
        print(response)
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
