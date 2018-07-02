
import urllib
from django.db import models
from django.db.models import Q
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from architect import utils


class Manager(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    engine = models.CharField(max_length=32, default='saltstack')
    metadata = JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)
    status = models.CharField(max_length=32, default='unknown')

    def __str__(self):
        return self.name

    def client(self):
        client_class = utils.get_module(self.engine, 'manager')
        return client_class(**{
            'name': self.name,
            'engine': self.engine,
            'metadata': self.metadata})

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
        return Resource.objects.filter(manager=self)

    def get_resources_count(self):
        return Resource.objects.filter(manager=self).count

    def get_active_resources(self):
        return Resource.objects.filter(manager=self, status='active')

    def get_error_resources(self):
        return Resource.objects.filter(manager=self, status='error')

    def get_unknown_resources(self):
        return Resource.objects.filter(manager=self, status='unknown')

    def resources_by_kind(self):
        kinds = self.get_schema()['resource']
        output = {}
        for kind in kinds:
            output[kind] = Resource.objects.filter(manager=self, kind=kind)
        return output

    def conn_detail(self):
        if self.metadata is None:
            return '-'
        elif self.engine == 'amazon':
            return 'Access key: {} ({} region)'.format(self.metadata.get('aws_access_key_id', '-'),
                                    self.metadata.get('region', '-'))
        elif self.engine in ['jenkins', 'saltstack', 'spinnaker']:
            return 'URL: {}'.format(self.metadata.get('auth_url', '-'))
        elif self.engine == 'heat':
            return 'Cloud: {}'.format(self.metadata.get('cloud_endpoint', '-'))
        elif self.engine == 'helm':
            return 'Cluster: {}'.format(self.metadata.get('container_endpoint', '-'))
        elif self.engine == 'homeassistant':
            return 'URL: https://{}:{}'.format(self.metadata['host'], self.metadata.get('port', 8123))
        elif self.engine == 'kubernetes':
            return 'URL: {}'.format(self.metadata.get('cluster', {}).get('server', '-'))
        elif self.engine == 'openstack':
            return 'URL: {}'.format(self.metadata.get('auth', {}).get('auth_url', '-'))
        elif self.engine == 'terraform':
            return 'Path: {}'.format(self.metadata.get('template_path', '-'))
        else:
            return '-'

    class Meta:
        ordering = ['name']


class Resource(models.Model):
    uid = models.CharField(max_length=511)
    name = models.CharField(max_length=511)
    manager = models.ForeignKey(Manager,
                                on_delete=models.CASCADE,
                                related_name='resources')
    kind = models.CharField(max_length=32)
    size = models.IntegerField(default=1)
    metadata = JSONField(encoder=DjangoJSONEncoder, blank=True, null=True)
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

    def workflow_options(self):
        return self.manager.client()._schema['resource'][self.kind].get('workflow')

    class Meta:
        ordering = ['name']


class Relationship(models.Model):
    manager = models.ForeignKey(Manager, on_delete=models.CASCADE)
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
