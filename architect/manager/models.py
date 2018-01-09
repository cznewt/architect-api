
from django.db import models
from yamlfield.fields import YAMLField


class Manager(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    engine = models.CharField(max_length=32, default='saltstack')
    metadata = YAMLField(blank=True, null=True)
    status = models.CharField(max_length=32, default='unknown')

    def __str__(self):
        return self.name

    def url(self):
        if self.engine == 'saltstack':
            return self.metadata.get('auth_url', '-')
        elif self.engine == 'kubernetes':
            return self.metadata.get('cluster', {}).get('server', '-')
        elif self.engine == 'openstack':
            return self.metadata.get('auth', {}).get('auth_url', '-')
        else:
            return '-'


class Resource(models.Model):
    uid = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    manager = models.ForeignKey(Manager, on_delete=models.CASCADE)
    kind = models.CharField(max_length=32)
    size = models.IntegerField(default=1)
    metadata = YAMLField(blank=True, null=True)
    status = models.CharField(max_length=32, default='unknown')

    def __str__(self):
        return self.name




class Relationship(models.Model):
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
        return self.id
