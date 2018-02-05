import re
import pyaml
from django import template

register = template.Library()


@register.filter(name='to_yaml')
def to_yaml(value):
    """
    Output value as YAML string
    """
    return pyaml.dump(value)


@register.filter(name='lcut')
def lcut(value, pattern):
    """
    Cuts 'pattern' in 'value', if 'value' starts with 'pattern'.
    """
    return re.sub('^%s' % pattern, '', value)


@register.filter(name='rcut')
def rcut(value, pattern):
    """
    Cuts 'pattern' in 'value', if 'value' ends with 'pattern'.
    """
    return re.sub('%s$' % pattern, '', value)
