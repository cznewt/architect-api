
import os
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML
from django import forms
from django.urls import reverse
from django.core import validators
from .models import Repository


class SlugField(forms.CharField):
    default_validators = [validators.validate_slug]


class RepositoryDeleteForm(forms.Form):

    repository_name = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(RepositoryDeleteForm, self).__init__(*args, **kwargs)
        repository_name = self.initial.get('repository_name')
        delete_url = reverse('repository:repository_delete',
                             kwargs={'repository_name': repository_name})
        self.label = 'Delete repository'
        self.modal_class = 'modal-sm'
        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.helper.form_action = delete_url
        self.helper.layout = Layout(
            Div(
                Div(
                    Div('repository_name', css_class='col-md-12'),
                    css_class='form-row'),
                HTML('<h6>Are you sure to delete <span class="badge badge-warning">{}</span> ?</h6>'.format(repository_name)),
                css_class='modal-body',
            ),
            Div(
                Submit('submit', 'Submit', css_class='btn border-primary'),
                css_class='modal-footer',
            )
        )

    def handle(self):
        data = self.clean()
        repository = Repository.objects.get(name=data.get('repository_name'))
        repository.delete()


class RepositoryCreateForm(forms.Form):

    repository_name = forms.CharField(label="Repository name")
    display_name = forms.CharField(required=False, label="Display name")
    repository_engine = forms.ChoiceField(
        choices=(
            ('bbb', 'BeagleBone images'),
            ('rpi', 'RaspberryPi images'),
            ('esp', 'ESP MicroPython images'),
            ('packer', 'Packer images'),
        ))
    image_dir = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(RepositoryCreateForm, self).__init__(*args, **kwargs)
        create_url = reverse('repository:repository_create')
        self.label = 'Create new repository'
        self.modal_class = 'modal-lg'
        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.helper.form_action = create_url
        self.helper.layout = Layout(
            Div(
                Div(
                    Div('repository_name', css_class='col-md-6'),
                    Div('display_name', css_class='col-md-6'),
                    css_class='form-row'),
                Div(
                    Div('repository_engine', css_class='col-md-6'),
                    Div('image_dir', css_class='col-md-6'),
                    css_class='form-row'),
            ),
            Div(
                Submit('submit', 'Create', css_class='btn border-primary'),
                css_class='modal-footer',
            )
        )

    def clean_repository_name(self):
        repository_name = self.cleaned_data['repository_name']
        if Repository.objects.filter(name=repository_name).count() > 0:
            raise forms.ValidationError(
                "Repository with this name already exists."
            )
        return repository_name

    def handle(self):
        if not os.path.exists(self.cleaned_data['image_dir']):
            os.makedirs(self.cleaned_data['image_dir'])
        kwargs = {
            'name': self.cleaned_data['repository_name'],
            'engine': self.cleaned_data['repository_name'],
            'status': 'active',
            'metadata': {
                'name': self.cleaned_data['repository_name'],
                'image_dir': self.cleaned_data['image_dir'],
            }
        }
        repository = Repository(**kwargs)
        repository.save()
