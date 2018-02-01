
import os
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit
from django import forms
from django.urls import reverse
from django.core import validators
from .models import Inventory
from django.conf import settings


class SlugField(forms.CharField):
    default_validators = [validators.validate_slug]


class InventoryDeleteForm(forms.Form):

    inventory_name = forms.CharField()

    def __init__(self, *args, **kwargs):
        super(InventoryDeleteForm, self).__init__(*args, **kwargs)
        delete_url = reverse('inventory:inventory_delete',
                             kwargs={'inventory_name': self.initial.get('inventory_name')})
        self.helper = FormHelper()
        self.helper.form_id = 'inventory-delete'
        self.helper.form_action = delete_url
        self.helper.layout = Layout(
            Div(
                Div(
                    Div('inventory_name', css_class='col-md-12'),
                    css_class='form-row'),
                css_class='modal-body',
            ),
            Div(
                Submit('submit', 'Submit', css_class='btn border-primary'),
                css_class='modal-footer',
            )
        )

    def handle(self):
        data = self.clean()
        print(data)
        inventory = Inventory.objects.get(name=data.get('inventory_name'))
        inventory.delete()


class SaltFormulasInventoryCreateForm(forms.Form):

    inventory_name = forms.SlugField(label="Slug name")
    display_name = forms.SlugField(required=False, label="Display name")
    cluster_name = forms.SlugField(required=False)
    cluster_domain = forms.SlugField(required=False)
    class_dir = forms.ChoiceField(choices=settings.INVENTORY_RECLASS_CLASSES_DIRS)
    formula_dir = forms.ChoiceField(choices=settings.INVENTORY_SALT_FORMULAS_DIRS)

    def __init__(self, *args, **kwargs):
        super(SaltFormulasInventoryCreateForm, self).__init__(*args, **kwargs)
        create_url = reverse('inventory:inventory_create')
        self.helper = FormHelper()
        self.helper.form_id = 'inventory-create'
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
                        Div('formula_dir', css_class='col-md-6'),
                        css_class='form-row'),
                ),
                css_class='modal-body',
            ),
            Div(
                Submit('submit', 'Submit', css_class='btn border-primary'),
                css_class='modal-footer',
            )
        )

    def handle(self):

        data_dir = '{}/{}'.format(settings.INVENTORY_BASE_DIR,
                                  self.cleaned_data['inventory_name'])
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        kwargs = {
            'name': self.cleaned_data['inventory_name'],
            'engine': 'salt-formulas',
            'metadata': {
                'name': self.cleaned_data['inventory_name'],
                'cluster_name': self.cleaned_data['cluster_name'],
                'cluster_domain': self.cleaned_data['cluster_domain'],
                'class_dir': self.cleaned_data['class_dir'],
                'formula_dir': self.cleaned_data['formula_dir'],
                'node_dir': data_dir,
                'cluster_class_dir': None,
                'service_class_dir': None,
                'system_class_dir': None,
            }
        }
        if 'cluster_name' in self.cleaned_data:
            kwargs['metadata']['cluster_name'] = self.cleaned_data['cluster_name']
        if 'cluster_domain' in self.cleaned_data:
            kwargs['metadata']['cluster_domain'] = self.cleaned_data['cluster_domain']
        inventory = Inventory(**kwargs)
        inventory.save()
