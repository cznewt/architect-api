
from django.db import models
from django.db.models import Q
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

    def get_schema(self):
        return utils.get_resource_schema(self.engine)

    def get_resources(self):
        return Resource.objects.filter(monitor=self)

    def get_resources_count(self):
        return Resource.objects.filter(monitor=self).count

    def get_active_resources(self):
        return Resource.objects.filter(monitor=self, status='active')

    def get_error_resources(self):
        return Resource.objects.filter(monitor=self, status='error')

    def get_unknown_resources(self):
        return Resource.objects.filter(monitor=self, status='unknown')

    def resources_by_kind(self):
        kinds = self.get_schema()['resource']
        output = {}
        for kind in kinds:
            output[kind] = Resource.objects.filter(manager=self, kind=kind)
        return output

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
    sources = models.ManyToManyField(
        'Resource',
        related_name='resource_sources',
        through='Relationship',
        through_fields=('target', 'source'),
    )
    targets = models.ManyToManyField(
        'Resource',
        related_name='resource_targets',
        through='RelationshipProxy',
        through_fields=('source', 'target'),
    )

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

    def relations(self):
        return Relationship.objects.filter(Q(source=self) | Q(target=self))

    def distinct_sources(self):
        output = {}
        output_list = []
        data = Relationship.objects.filter(target=self)
        for datum in data:
            if datum.source.uid not in output:
                output[datum.source.uid] = datum.source
        sorted_keys = sorted(output.keys(), key=lambda x: x.lower())
        for key in sorted_keys:
            output_list.append(output[key])
        return output_list

    def workflow_options(self):
        return self.monitor.client()._schema['resource'][self.kind].get('workflow')

    class Meta:
        ordering = ['name']


class Relationship(models.Model):
    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE)
    source = models.ForeignKey(Resource,
                               on_delete=models.CASCADE,
                               related_name='source')
    target = models.ForeignKey(Resource,
                               on_delete=models.CASCADE,
                               related_name='destination')
    kind = models.CharField(max_length=32)
    size = models.IntegerField(default=1)
    metadata = JSONField(blank=True, null=True)
    status = models.CharField(max_length=32, default='unknown')

    def __str__(self):
        return '{} > {}'.format(self.source, self.target)

    def name(self):
        return self.__str__()


class RelationshipProxy(Relationship):
    class Meta:
        proxy = True
