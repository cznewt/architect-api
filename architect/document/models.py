
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.translation import gettext_lazy as _


class Document(models.Model):
    name = models.CharField(verbose_name=_("Document name"),
                            max_length=255)
    description = models.TextField(blank=True,
                                   null=True)
    engine = models.CharField(verbose_name=_("Engine"),
                              max_length=32,
                              default='dashboard')
    metadata = JSONField(blank=True,
                         null=True)
    status = models.CharField(verbose_name=_("Status"),
                              max_length=32,
                              default='active')

    def widgets(self):
        return self.metadata.get('widget', {})

    def add_widget(self, widget_name, widget_meta):
        self.metadata['widget'][widget_name] = widget_meta

    def color(self):
        if self.status == 'active':
            return 'success'
        if self.status == 'error':
            return 'danger'
        if self.status == 'build':
            return 'info'
        else:
            return 'warning'

    def __str__(self):
        return self.name
