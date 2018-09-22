from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Resource, Manager


def validate_manager_name(value):
    managers = Manager.objects.filter(name=value)
    if managers.count() > 0:
        raise ValidationError('Manager with name "{}" already exists.'.format(value), code='invalid')
