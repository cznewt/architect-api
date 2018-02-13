
from architect import utils
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe
from yamlfield.fields import YAMLField


class Inventory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    engine = models.CharField(max_length=32, default='reclass')
    metadata = YAMLField(blank=True, null=True)
    status = models.CharField(max_length=32, default='unknown')

    def client(self):
        client_class = utils.get_module(self.engine, 'inventory')
        return client_class(**{
            'name': self.name,
            'engine': self.engine,
            'metadata': self.metadata})

    def class_list(self, resource=None):
        return self.client().class_list(resource=None)

    def inventory(self, resource=None):
        return self.client().inventory(resource=None)

    def resource_count(self, resource=None):
        return len(self.client().inventory(resource=None))

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
        elif self.engine in ['reclass', 'salt-formulas']:
            return mark_safe("{}<br/>{}".format(self.metadata.get('node_dir', '-'),
                                                self.metadata.get('class_dir', '-')))
        else:
            return '-'

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Inventories"
        ordering = ['name']


class Resource(models.Model):
    uid = models.CharField(max_length=511)
    name = models.CharField(max_length=511)
    inventory = models.ForeignKey(Inventory,
                                  on_delete=models.CASCADE,
                                  related_name='resources')
    kind = models.CharField(max_length=32)
    size = models.IntegerField(default=1)
    metadata = YAMLField(blank=True, null=True)
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
