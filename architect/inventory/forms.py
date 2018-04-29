
import os
import re
from jinja2 import Environment
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
        if resource.kind == 'reclass_node':
            filepath = os.path.join(inventory.metadata['node_dir'], resource.metadata['__reclass__']['uri'].replace('yaml_fs://', ''))
            print(filepath)
            if os.path.isfile(filepath):
                os.remove(filepath)
        resource.delete()


class BootstrapFormMixin(object):

    def __init__(self, *args, **kwargs):
        super(BootstrapFormMixin, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class ResourceCreateForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.inventory = kwargs.pop('inventory')
        self.form_meta = kwargs.pop('form_meta')
        parameters = kwargs.pop('params')
        form_name = kwargs.pop('form_name')
        super(ResourceCreateForm, self).__init__(*args, **kwargs)

        action_url = reverse('inventory:model_generate',
                             kwargs={'inventory_name': self.inventory.name,
                                     'form_name': form_name})
        layout_fields = []

        for param in parameters:
            kwargs = {}
            if 'label' in param:
                kwargs['label'] = param['label']
            else:
                kwargs['label'] = param['name']
            if 'help_text' in param:
                kwargs['help_text'] = param['help_text']

            if param.get('value_type', 'string') == 'string':
                field = forms.CharField(**kwargs)

            self.fields[param['name']] = field
            layout_fields.append(param['name'])

        self.label = self.form_meta.get('name', form_name)
        self.modal_class = 'modal-{}'.format(self.form_meta.get('size', 'sm'))
        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.helper.form_action = action_url
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(*layout_fields, css_class='col-md-12'),
                    css_class='form-row'),
                css_class='modal-body',
            ),
            Div(
                Submit('submit', 'Submit', css_class='btn border-primary'),
                css_class='modal-footer',
            )
        )

    def clean(self):
        cleaned_data = super(ResourceCreateForm, self).clean()
        templates = {}
        for template in self.form_meta.get('templates', []):
            filename = Environment().from_string(template['file']).render(cleaned_data)
            content = Environment().from_string(template['content']).render(cleaned_data)
            filepath = os.path.join(self.inventory.metadata['node_dir'], filename)
            if os.path.isfile(filepath):
                raise forms.ValidationError(
                    'Generated file already exists: %(filename)s',
                    code='invalid',
                    params={'filename': filename},
                )

        return cleaned_data

    def handle(self):
        config_context = self.clean()
        templates = {}
        for template in self.form_meta.get('templates', []):
            filename = Environment().from_string(template['file']).render(config_context)
            content = Environment().from_string(template['content']).render(config_context)
            templates[filename] = content

        for filename, content in templates.items():
            with open(self.get_config_file(config_context['image_name']), "w+") as file_handler:
                file_handler.write(config_content)
