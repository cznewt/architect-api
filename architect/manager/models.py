
from django.db import models
from django.db.models import Q
from yamlfield.fields import YAMLField
from architect import utils


class Manager(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    engine = models.CharField(max_length=32, default='saltstack')
    metadata = YAMLField(blank=True, null=True)
    status = models.CharField(max_length=32, default='unknown')

    def __str__(self):
        return self.name

    def client(self):
        client_class = utils.get_module(self.engine, 'manager')
        return client_class(**{
            'name': self.name,
            'engine': self.engine,
            'metadata': self.metadata})

    def get_schema(self):
        return utils.get_resource_schema(self.engine)

    def resources_by_kind(self):
        kinds = self.get_schema()['resource']
        output = {}
        for kind in kinds:
            output[kind] = Resource.objects.filter(manager=self, kind=kind)
        return output

    def url(self):
        if self.metadata is None:
            return '-'
        elif self.engine == 'saltstack':
            return self.metadata.get('auth_url', '-')
        elif self.engine == 'kubernetes':
            return self.metadata.get('cluster', {}).get('server', '-')
        elif self.engine == 'openstack':
            return self.metadata.get('auth', {}).get('auth_url', '-')
        else:
            return '-'


class Resource(models.Model):
    uid = models.CharField(max_length=511)
    name = models.CharField(max_length=511)
    manager = models.ForeignKey(Manager, on_delete=models.CASCADE)
    kind = models.CharField(max_length=32)
    size = models.IntegerField(default=1)
    metadata = YAMLField(blank=True, null=True)
    status = models.CharField(max_length=32, default='unknown')

    def __str__(self):
        return '{} {}'.format(self.kind, self.name)

    def relations(self):
        return Relationship.objects.filter(Q(source=self) | Q(target=self))


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
    metadata = YAMLField(blank=True, null=True)
    status = models.CharField(max_length=32, default='unknown')

    def __str__(self):
        return '{} > {}'.format(self.source, self.target)

    def name(self):
        return self.__str__()
