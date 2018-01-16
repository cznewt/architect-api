# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.apps import AppConfig
from material.frontend.apps import ModuleMixin


class ArchitectMonitorConfig(ModuleMixin, AppConfig):
    name = 'monitor'
    verbose_name = 'Architect Monitor'
