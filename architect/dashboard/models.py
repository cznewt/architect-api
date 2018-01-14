
from django.db import models
from yamlfield.fields import YAMLField


class Dashboard(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    metadata = YAMLField(blank=True, null=True)
    status = models.CharField(max_length=32, default='unknown')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Inventories"
