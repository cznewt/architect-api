# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.apps import AppConfig
from material.frontend.apps import ModuleMixin


class ArchitectManagerConfig(ModuleMixin, AppConfig):
    name = 'manager'
    verbose_name = 'Architect Manager'
