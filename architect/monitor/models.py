
from django.db import models
from yamlfield.fields import YAMLField


class Monitor(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    metadata = YAMLField(blank=True, null=True)
    status = models.CharField(max_length=32, default='active')

    def widgets(self):
        return self.metadata.get('widget', {})

    def __str__(self):
        return self.name
