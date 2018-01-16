
import os
import re
import json
import yaml
import importlib

from django.conf import settings
from architect import exceptions

_schema_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'schemas')


def load_yaml_json_file(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            if path.endswith('json'):
                return json.load(f)
            else:
                return yaml.safe_load(f)
    return {}


def get_node_icon(icon):
    family, character = icon.split(":")
    icon_file = os.path.join(_schema_dir, '_icon.yaml')
    icon_mapping = load_yaml_json_file(icon_file)
    output = icon_mapping['character'][family][character].copy()
    output["family"] = icon_mapping['family'][family]
    output['name'] = character
    output["char"] = int("0x{}".format(output["char"]), 0)
    return output


def get_resource_schema(name):
    schema_file = os.path.join(_schema_dir, '{}.yaml'.format(name))
    return load_yaml_json_file(schema_file)


def to_camel_case(snake_str, first=True):
    components = snake_str.split('_')
    if first:
        return "".join(x.title() for x in components)
    else:
        return components[0] + "".join(x.title() for x in components[1:])


def to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_module(module_key, module_type='manager'):
    if module_type == 'manager':
        class_mapping = settings.MANAGER_CLASS_MAPPINGS
    elif module_type == 'inventory':
        class_mapping = settings.INVENTORY_CLASS_MAPPINGS
    if module_key not in class_mapping:
        raise exceptions.ArchitectException(
            "Service {module_key} is unkown. Please pass in a client"
            " constructor or submit a patch to Architect".format(
                module_key=module_key))
    mod_name, ctr_name = class_mapping[module_key].rsplit('.', 1)
    lib_name = mod_name.split('.')[0]
    try:
        mod = importlib.import_module(mod_name)
    except ImportError:
        raise exceptions.ArchitectException(
            "Client for '{module_key}' was requested, but"
            " {mod_name} was unable to be imported. Either import"
            " the module yourself and pass the constructor in as an argument,"
            " or perhaps you do not have module {lib_name} installed.".format(
                module_key=module_key,
                mod_name=mod_name,
                lib_name=lib_name))
    try:
        ctr = getattr(mod, ctr_name)
    except AttributeError:
        raise exceptions.ArchitectException(
            "Client for '{module_key}' was requested, but although"
            " {mod_name} imported fine, the constructor at {fullname}"
            " as not found.".format(
                module_key=module_key,
                mod_name=mod_name,
                fullname=class_mapping[module_key]))
    return ctr


class ClassRegistry:

    def __init__(self):
        self._classes = {}

    def add(self, cls):
        self._classes[cls.__name__] = cls

    def get_type(self, name):
        return self._classes.get(name)
