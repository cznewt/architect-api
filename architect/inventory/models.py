
from django.db import models
from yamlfield.fields import YAMLField
from architect import utils


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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Inventories"
