
import os
import uuid
import time
import datetime
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML
from django import forms
from django.urls import reverse
from django.core import validators
from .tasks import generate_image_task
from .models import Repository, Resource
from architect.inventory.models import Inventory, Resource as InventoryResource
from architect.manager.models import Manager, Resource as ManagerResource
from architect.manager.tasks import process_resource_action_task


class SlugField(forms.CharField):
    default_validators = [validators.validate_slug]

KEY_CHOICES=[('keep', "Reuse keypair from last image build"),
             ('generate','Generate and only accept new keypair'),
             ('force_generate','Generate and force accept new keypair')]

class ImageCreateForm(forms.Form):

    key_strategy = forms.ChoiceField(label="Key management",
                                     choices=KEY_CHOICES,
                                     widget=forms.RadioSelect(),
                                     initial='keep',
                                     help_text="If you force generate new keypair for node that is active, you will loose connection to this running node. You cannot reuse keypair if no image for given node exists.")

    def __init__(self, *args, **kwargs):
        super(ImageCreateForm, self).__init__(*args, **kwargs)
        repository_name = self.initial.get('repository_name')
        create_url = reverse('repository:image_create',
                             kwargs={'repository_name': repository_name})
        repository = Repository.objects.get(name=repository_name)
        inventory = Inventory.objects.get(name=repository.metadata['inventory'])
        nodes = InventoryResource.objects.filter(inventory=inventory).order_by('name')
        hostname_choices = []
        for node in nodes:
            hostname_choices.append((node.name, node.name))
        self.fields['type'] = forms.ChoiceField(label='Image Type',
                                                choices=repository.client().get_image_types(),
                                                help_text="Select hardware definion for the new image.")
        self.fields['hostname'] = forms.ChoiceField(label='Node',
                                                    choices=hostname_choices,
                                                    help_text="Select node from {} inventory.".format(inventory.name))
        self.label = 'Create New Image in {} Repository'.format(repository_name)
        self.modal_class = 'modal-lg'

        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.helper.form_action = create_url
        self.helper.layout = Layout(
            Div(
                Div(
                    Div('type', css_class='col-md-6'),
                    Div('hostname', css_class='col-md-6'),
                    css_class='form-row'),
                Div(
                    Div('key_strategy', css_class='col-md-12'),
                    css_class='form-row'),
                css_class='modal-body',
            ),
            Div(
                Submit('submit', 'Create', css_class='btn border-primary'),
                css_class='modal-footer',
            )
        )

    def handle(self):
        data = self.clean()
        key_strategy = data.pop('key_strategy')
        now = datetime.datetime.now()
        data['create_time'] = time.mktime(now.timetuple())
        repository_name = self.initial.get('repository_name')
        repository = Repository.objects.get(name=repository_name)
        image_uuid = str(uuid.uuid4())
        image_name = '{}-{}'.format(data['hostname'],
                                    now.strftime('%Y%m%d%H%M%S'))
        kwargs = {
            'uid': image_uuid,
            'name': image_name,
            'repository': repository,
            'kind': 'image',
            'status': 'build',
            'metadata': data,
        }
        resource = Resource(**kwargs)
        resource.save()

        data['image_uid'] = image_uuid
        data['image_name'] = image_name

        manager = Manager.objects.get(name=repository.metadata['manager'])
        if key_strategy == 'keep':
            last_images = Resource.objects.filter(name__contains='{}-'.format(data['hostname'])).order_by('-id')
            for last_image in last_images:
                if 'config' in last_image.metadata:
                    data['config'] = last_image.metadata['config']
                    break
        else:
            if key_strategy == 'force_generate':
                force = True
            else:
                force = False
            salt_master = ManagerResource.objects.get(manager=manager, kind='salt_master')
            keys = process_resource_action_task.apply((manager.name,
                                                    salt_master.uid,
                                                    'generate_key',
                                                    {'minion_id': data['hostname'],
                                                     'force': force}))
            data['config'] = {
                'master': '127.0.0.1',
                'pub_key': keys.result['pub'],
                'priv_key': keys.result['priv']
            }

        resource.metadata['config'] = data['config']
        resource.save()

        generate_image_task.apply_async((repository_name,
                                         data))

class ImageDeleteForm(forms.Form):

    confirm = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        self.repository_name = kwargs.pop('repository_name')
        self.image_name = kwargs.pop('image_name')
        super(ImageDeleteForm, self).__init__(*args, **kwargs)
        delete_url = reverse('repository:image_delete',
                             kwargs={'repository_name': self.repository_name,
                                     'image_name': self.image_name})
        self.label = 'Delete Image {}?'.format(self.image_name)
        self.modal_class = 'modal-md'
        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.helper.form_action = delete_url
        self.helper.layout = Layout(
            Div(
                Div(
                    Div('confirm', css_class='col-md-12'),
                    css_class='form-row'),
                HTML('<p>Are you sure to delete image <span class="badge badge-warning">{}</span> from repository {}?</p><p>This action cannot be reversed.</p>'.format(self.image_name, self.repository_name)),
                css_class='modal-body',
            ),
            Div(
                Submit('submit', 'Commit Delete', css_class='btn border-primary'),
                css_class='modal-footer',
            )
        )

    def handle(self):
        data = self.clean()
        repository = Repository.objects.get(name=self.repository_name)
        image = Resource.objects.get(name=self.image_name, repository=repository)
        repository.client().delete_image(image.name)
        image.delete()


class RepositoryCreateForm(forms.Form):

    repository_name = forms.CharField(label="Repository name")
    display_name = forms.CharField(required=False, label="Display name")
    repository_engine = forms.ChoiceField(
        choices=(
            ('bbb', 'BeagleBone images'),
            ('rpi23', 'RaspberryPi images'),
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
