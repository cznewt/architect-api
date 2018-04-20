
import yaml
from django import forms
from django.urls import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit, HTML
from django.conf import settings
from django.core import validators
from architect.inventory.models import Inventory, Resource


class NodeCreateForm(forms.Form):

    name = forms.CharField(label="Name",
                           initial='node01')
    domain = forms.CharField(label="Domain",
                             initial='domain.com')
    cluster = forms.CharField(label="Cluster",
                              initial='default')
    environment = forms.CharField(label="Environment",
                                  initial='prd')
    params = forms.CharField(label="Parameters",
                             widget=forms.Textarea(attrs={'cols': 80, 'rows': 7}),
                             required=False,
                             help_text="Dictionary of node level parameters in YAML format.")
    classes = forms.CharField(label="Classes",
                              widget=forms.Textarea(attrs={'cols': 80, 'rows': 7}),
                              required=False,
                              help_text="List of metadata classes node implements in YAML format.")

    def __init__(self, *args, **kwargs):
        print(kwargs)
        self.inventory = Inventory.objects.get(name=kwargs.pop('inventory'))
        super(NodeCreateForm, self).__init__(*args, **kwargs)
        action_url = reverse('inventory:node_create',
                             kwargs={'inventory_name': self.inventory.name})
        self.label = "Create New Node Definition at {} Inventory".format(self.inventory.name)
        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.modal_class = 'modal-lg'
        self.helper.form_action = action_url
        self.helper.layout = Layout(
            Div(
                Div(
                    Div('name', css_class='col-md-6'),
                    Div('domain', css_class='col-md-6'),
                    css_class='form-row'),
                Div(
                    Div('cluster', css_class='col-md-6'),
                    Div('environment', css_class='col-md-6'),
                    css_class='form-row'),
                Div(
                    Div('params', css_class='col-md-6'),
                    Div('classes', css_class='col-md-6'),
                    css_class='form-row'),
                css_class='modal-body',
            ),
            Div(
                Submit('submit', 'Submit', css_class='btn border-primary'),
                css_class='modal-footer',
            )
        )

    def handle(self):
        data = self.cleaned_data
        classes = yaml.load(data.pop('classes'))
        parameters = yaml.load(data.pop('params'))

        node_name = '{}.{}'.format(data.get('name'),
                                   data.get('domain'))
        node_metadata = {
            'classes': classes,
            'parameters': {
                '_param': parameters,
                'linux': {
                    'system': data
                }
            }
        }
        self.inventory.client().resource_create(node_name, node_metadata)
        self.inventory.client().update_resources()


class NodeUpdateForm(forms.Form):

    raw_metadata = forms.CharField(label="Raw Metadata",
                                   widget=forms.Textarea(attrs={'cols': 80, 'rows': 12}))

    def __init__(self, *args, **kwargs):
        print(kwargs)
        self.inventory = Inventory.objects.get(name=kwargs.pop('inventory_name'))
        self.node = Resource.objects.get(name=kwargs.pop('node_name'),
                                         inventory=self.inventory)
        super(NodeUpdateForm, self).__init__(*args, **kwargs)
        action_url = reverse('inventory:node_update',
                             kwargs={'inventory_name': self.inventory.name,
                                     'node_name': self.node.name})
        self.label = "Update Node {} Definition at {} Inventory".format(self.node.name,
                                                                        self.inventory.name)
        self.fields['raw_metadata'].initial = yaml.dump(self.node.metadata)
        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.modal_class = 'modal-lg'
        self.helper.form_action = action_url
        self.helper.layout = Layout(
            Div(
                Div(
                    Div('raw_metadata', css_class='col-md-12'),
                    css_class='form-row'
                ),
                css_class='modal-body'
            ),
            Div(
                Submit('submit', 'Submit', css_class='btn border-primary'),
                css_class='modal-footer'
            )
        )

    def handle(self):
        data = self.cleaned_data
        classes = yaml.load(data.pop('classes'))
        parameters = yaml.load(data.pop('params'))

        node_name = '{}.{}'.format(data.get('name'),
                                   data.get('domain'))
        node_metadata = {
            'classes': classes,
            'parameters': {
                '_param': parameters,
                'linux': {
                    'system': data
                }
            }
        }
        self.inventory.client().resource_create(node_name, node_metadata)
        self.inventory.client().update_resources()


class InventoryCreateForm(forms.Form):

    inventory_name = forms.CharField(label="Inventory name")
    display_name = forms.CharField(required=False, label="Display name")
    cluster_name = forms.SlugField(required=False)
    cluster_domain = forms.CharField(required=False)
    class_dir = forms.ChoiceField(
        choices=settings.INVENTORY_RECLASS_CLASSES_DIRS)

    def __init__(self, *args, **kwargs):
        super(InventoryCreateForm, self).__init__(*args, **kwargs)
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
