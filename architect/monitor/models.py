
from django.db import models
from django.contrib.postgres.fields import JSONField
from architect import utils


class Monitor(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    engine = models.CharField(max_length=32, default='prometheus')
    metadata = JSONField(blank=True, null=True)
    status = models.CharField(max_length=32, default='active')

    def client(self):
        client_class = utils.get_module(self.engine, 'monitor')
        return client_class(**{
            'name': self.name,
            'engine': self.engine,
            'metadata': self.metadata})

    def widgets(self):
        return self.metadata.get('widget', {})

    def color(self):
        if self.status == 'active':
            return 'success'
        if self.status == 'error':
            return 'danger'
        if self.status == 'build':
            return 'info'
        else:
            return 'warning'

    def conn_detail(self):
        if self.metadata is None:
            return '-'
        elif self.engine in ['graphite', 'influxdb', 'prometheus']:
            return self.metadata.get('auth_url', '-')
        else:
            return '-'

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Resource(models.Model):
    uid = models.CharField(max_length=511)
    name = models.CharField(max_length=511)
    monitor = models.ForeignKey(Monitor,
                                on_delete=models.CASCADE,
                                related_name='resources')
    kind = models.CharField(max_length=32)
    size = models.IntegerField(default=1)
    metadata = JSONField(blank=True, null=True)
    status = models.CharField(max_length=32, default='unknown')

    def __str__(self):
        return '{} {}'.format(self.kind, self.name)

    def color(self):
        if self.status == 'active':
            return 'success'
        if self.status == 'error':
            return 'danger'
        if self.status == 'build':
            return 'info'
        else:
            return 'warning'

    class Meta:
        ordering = ['name']
