
import os
import re
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit, HTML
from django import forms
from django.urls import reverse
from django.conf import settings
from django.core import validators
from .models import Inventory, Resource


class SlugField(forms.CharField):
    default_validators = [validators.validate_slug]


class InventoryDeleteForm(forms.Form):

    inventory_name = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(InventoryDeleteForm, self).__init__(*args, **kwargs)
        inventory_name = self.initial.get('inventory_name')
        delete_url = reverse('inventory:inventory_delete',
                             kwargs={'inventory_name': inventory_name})
        self.label = 'Delete inventory'
        self.modal_class = 'modal-sm'
        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.helper.form_action = delete_url
        self.helper.layout = Layout(
            Div(
                Div(
                    Div('inventory_name', css_class='col-md-12'),
                    css_class='form-row'),
                HTML('<h6>Are you sure to delete <span class="badge badge-warning">{}</span> ?</h6>'.format(inventory_name)),
                css_class='modal-body',
            ),
            Div(
                Submit('submit', 'Submit', css_class='btn border-primary'),
                css_class='modal-footer',
            )
        )

    def handle(self):
        data = self.clean()
        inventory = Inventory.objects.get(name=data.get('inventory_name'))
        inventory.delete()


class ResourceDeleteForm(forms.Form):

    inventory_name = forms.CharField(widget=forms.HiddenInput())
    resource_name = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(ResourceDeleteForm, self).__init__(*args, **kwargs)
        inventory_name = self.initial.get('inventory_name')
        resource_name = self.initial.get('resource_name')
        delete_url = reverse('inventory:resource_delete',
                             kwargs={'inventory_name': inventory_name,
                                     'resource_name': resource_name})
        self.label = 'Delete resource'
        self.modal_class = 'modal-sm'
        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.helper.form_action = delete_url
        self.helper.layout = Layout(
            Div(
                Div(
                    Div('inventory_name', css_class='col-md-12'),
                    Div('resource_name', css_class='col-md-12'),
                    css_class='form-row'),
                HTML('<h6>Are you sure to delete <span class="badge badge-warning">{}</span> ?</h6>'.format(resource_name)),
                css_class='modal-body',
            ),
            Div(
                Submit('submit', 'Submit', css_class='btn border-primary'),
                css_class='modal-footer',
            )
        )

    def handle(self):
        data = self.clean()
        inventory = Inventory.objects.get(name=data.get('inventory_name'))
        resource = Resource.objects.get(
            inventory=inventory, name=data.get('resource_name'))
        resource.delete()


class HierDeployInventoryCreateForm(forms.Form):

    inventory_name = forms.CharField(label="Inventory name")
    display_name = forms.CharField(required=False, label="Display name")
    cluster_name = forms.SlugField(required=False)
    cluster_domain = forms.CharField(required=False)
    class_dir = forms.ChoiceField(
        choices=settings.INVENTORY_RECLASS_CLASSES_DIRS)

    def __init__(self, *args, **kwargs):
        super(HierDeployInventoryCreateForm, self).__init__(*args, **kwargs)
        create_url = reverse('inventory:inventory_create')
        self.label = 'Create new hier-cluster inventory'
        self.help_text = 'Optional help text'
        self.modal_class = 'modal-lg'
        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.helper.form_action = create_url
        self.helper.layout = Layout(
            Div(
                Div(
                    Div('inventory_name', css_class='col-md-6'),
                    Div('display_name', css_class='col-md-6'),
                    css_class='form-row'),
                Fieldset(
                    'Initial data',
                    Div(
                        Div('cluster_name', css_class='col-md-6'),
                        Div('cluster_domain', css_class='col-md-6'),
                        css_class='form-row'),
                ),
                Fieldset(
                    'Directories',
                    Div(
                        Div('class_dir', css_class='col-md-6'),
                        css_class='form-row'),
                ),
                css_class='modal-body',
            ),
            Div(
                Submit('submit', 'Submit', css_class='btn border-primary'),
                css_class='modal-footer',
            )
        )

    def clean_inventory_name(self):
        inventory_name = self.cleaned_data['inventory_name']
        if Inventory.objects.filter(name=inventory_name).count() > 0:
            raise forms.ValidationError(
                "Inventory with this name already exists."
            )
        return inventory_name

    def clean_domain_name(self):
        domain_name = self.cleaned_data['domain_name']
        if len(domain_name) > 255:
            raise forms.ValidationError(
                "Domain name is too long (more than 255 chars)."
            )
        if domain_name[-1] == ".":
            domain_name = domain_name[:-1]
        allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
        if not all(allowed.match(x) for x in domain_name.split(".")):
            raise forms.ValidationError(
                "Domain name contains illegal characters."
            )
        return domain_name

    def clean(self):
        cleaned_data = super().clean()
        cluster_name = cleaned_data.get("cluster_name")
        class_dir = cleaned_data.get("class_dir")
        if cluster_name != '':
            cluster_dir = '{}/cluster/{}'.format(class_dir, cluster_name)
            print(cluster_dir)
            if not os.path.exists(cluster_dir):
                raise forms.ValidationError(
                    "Cluster {} is not defined in selected classes {}.".format(
                        cluster_name,
                        class_dir
                    )
                )
            if cleaned_data.get("cluster_domain") == '':
                raise forms.ValidationError(
                    "If cluster name is filled, you need fill domain as well."
                )

    def handle(self):
        data_dir = '{}/{}'.format(settings.INVENTORY_BASE_DIR,
                                  self.cleaned_data['inventory_name'])
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        kwargs = {
            'name': self.cleaned_data['inventory_name'],
            'engine': 'hier-deploy',
            'status': 'active',
            'metadata': {
                'name': self.cleaned_data['inventory_name'],
                'class_dir': self.cleaned_data['class_dir'],
                'node_dir': data_dir,
            }
        }
        if self.cleaned_data['cluster_name'] != '':
            kwargs['metadata']['cluster_name'] = self.cleaned_data['cluster_name']
            kwargs['metadata']['cluster_domain'] = self.cleaned_data['cluster_domain']
        inventory = Inventory(**kwargs)
        inventory.save()

        if self.cleaned_data['cluster_name'] != '' and \
           self.cleaned_data['cluster_domain'] != '':
            node_name = 'cfg01.{}'.format(self.cleaned_data['cluster_domain'])
            node_metadata = {
                'classes': [
                    'cluster.{}.infra.config'.format(
                        self.cleaned_data['cluster_name']),
                    'overrides.{}'.format(
                        self.cleaned_data['inventory_name'].replace('.', '-'))
                ],
                'parameters': {
                    '_param': {
                        'linux_system_codename': 'xenial'
                    },
                    'linux': {
                        'system': {
                            'name': 'cfg01',
                            'domain': self.cleaned_data['cluster_domain']
                        }
                    },
                    'salt': {
                        'master': {
                            'worker_threads': 10,
                            'pillar': {
                                'engine': 'architect'
                            },
                            'engine': {
                                'architect': {
                                    'engine': 'architect',
                                    'host': settings.PUBLIC_ENDPOINT,
                                    'port': '8181',
                                    'username': 'salt',
                                    'password': 'password',
                                    'project': self.cleaned_data['cluster_domain']
                                }
                            }
                        }
                    }
                }
            }
            inventory.client().resource_create(node_name, node_metadata)
            inventory.client().init_overrides()

            reclass_meta = inventory.client().inventory()[node_name]['parameters'].get('reclass', {}).get('storage', {})
            for node_name, node in reclass_meta.get('node', {}).items():
                node_name = '{}.{}'.format(node['name'], node['domain'])
                node_classes = node['classes'] + ['overrides.{}'.format(self.cleaned_data['inventory_name'].replace('.', '-'))]
                node_metadata = {
                    'classes': node_classes,
                    'parameters': {
                        '_param': node['params'],
                        'linux': {
                            'system': {
                                'name': node['name'],
                                'domain': node['domain']
                            }
                        }
                    }
                }
                inventory.client().resource_create(node_name, node_metadata)

            inventory.cache = {
                'class_mapping': reclass_meta.get('class_mapping', {}),
                'overrides': inventory.client().get_overrides()
            }
            inventory.save()
            inventory.client().update_resources()
