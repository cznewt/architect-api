
import yaml
from django import forms
from django.urls import reverse
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit, HTML
from .tasks import process_resource_action_task
from .models import Resource, Manager, Relationship
from .validators import validate_manager_name
from .tasks import sync_manager_resources_task

from django.utils.translation import ugettext as _


class ManagerActionForm(forms.Form):

    def __init__(self, *args, **kwargs):
        parameters = kwargs.pop('params')
        manager_name = kwargs.pop('manager_name')
        resource_kind = kwargs.pop('resource_kind')
        resource_action = kwargs.pop('resource_action')
        super().__init__(*args, **kwargs)
        action_url = reverse('manager:resource_action',
                             kwargs={'manager_name': manager_name,
                                     'resource_kind': resource_kind,
                                     'resource_action': resource_action})
        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.helper.form_action = action_url
        for param_name, param_field in parameters.items():
            self.fields[param_name] = param_field


class ResourceActionForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.manager = kwargs.pop('manager')
        self.resource = kwargs.pop('resource')
        self.action = kwargs.pop('action')
        parameters = kwargs.pop('params')
        super().__init__(*args, **kwargs)

        action_url = reverse('manager:resource_action',
                             kwargs={'manager_name': self.manager.name,
                                     'resource_uid': self.resource.id,
                                     'resource_action': self.action})
        layout_fields = []

        for param_name, param_field in parameters.items():
            self.fields[param_name] = param_field
            layout_fields.append(param_name)

        self.label = self.manager.client()._schema['resource'][self.resource.kind]['workflow'][self.action]['name']
        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.helper.form_action = action_url
        self.modal_class = 'modal-md'
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

    def handle(self):
        data = self.clean()
        process_resource_action_task.apply_async((self.manager.name,
                                                  self.resource.id,
                                                  self.action,
                                                  data))


class ManagerDeleteForm(forms.Form):

    manager_name = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(ManagerDeleteForm, self).__init__(*args, **kwargs)
        manager_name = self.initial.get('manager_name')
        delete_url = reverse('manager:manager_delete',
                             kwargs={'manager_name': manager_name})
        self.label = 'Delete manager'
        self.modal_class = 'modal-sm'
        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.helper.form_action = delete_url
        self.helper.layout = Layout(
            Div(
                Div(
                    Div('manager_name', css_class='col-md-12'),
                    css_class='form-row'),
                HTML('<h6>Are you sure to delete <span class="badge badge-warning">{}</span> ?</h6>'.format(manager_name)),
                css_class='modal-body',
            ),
            Div(
                Submit('submit', 'Submit', css_class='btn border-primary'),
                css_class='modal-footer',
            )
        )

    def handle(self):
        data = self.clean()
        manager = Manager.objects.get(name=data.get('manager_name'))
        manager.delete()


class ImportKubeconfigForm(forms.Form):

    name = forms.CharField(validators=[validate_manager_name])
    kubeconfig = forms.CharField(widget=forms.Textarea)
    context = forms.CharField(required=False)
    
    def __init__(self, *args, **kwargs):        
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.helper.form_action = reverse('manager:import_kubeconf')
        self.label = 'Import Kubeconfig'
        self.modal_class = 'modal-lg'

        self.helper.layout = Layout(
            Div(
                Div(
                    Div('name', css_class='col-md-6'),
                    Div('context', css_class='col-md-6'),
                    css_class='form-row'),
                Div(
                    Div('kubeconfig', css_class='col-md-12'),
                    css_class='form-row'),
                css_class='modal-body',
            ),
            Div(
                Submit('submit', 'Import', css_class='btn border-primary'),
                css_class='modal-footer',
            )
        )

    def clean(self):
        data = self.cleaned_data
        try:
            data['kubeconfig'] = yaml.safe_load(data['kubeconfig'])
        except yaml.parser.ParserError:
            data['kubeconfig'] = {'contexts': []}
            self.add_error('kubeconfig', _('Kubeconfig is not a valid YAML.'))
        if data['context'] != "":
            data['current_context'] = data['context']
        if len(data['kubeconfig'].get('contexts', [])) > 1:
            names = []
            for context in data['kubeconfig']['contexts']:
                names.append(context['name'])
            if data['context'] not in names:
                self.add_error('context', 'Multiple contexts found in kubeconfig, please select one of following: {}.'.format(', '.join(names)))
        elif len(data['kubeconfig'].get('contexts', [])) == 1:
            data['context'] == data['kubeconfig']['contexts'][0]['name']
        else:
            if data['context'] == "":
                if 'current-context' not in data['kubeconfig']:
                    self.add_error('context', 'No current-context found in kubeconfig, please select one.')
            data['context'] = data['kubeconfig'].get('current-context', 'default')
        return data

    def handle(self):
        data = self.cleaned_data
        current_context = None
        current_cluster = None
        current_user = None

        if len(data['kubeconfig'].get('contexts', [])) == 1:
            data_context = data['kubeconfig']['contexts'][0]['name']
        else:
            data_context = data['context']
        for context in data['kubeconfig']['contexts']:
            if context['name'] == data_context:
                current_context = context['context']
        for cluster in data['kubeconfig']['clusters']:
            if cluster['name'] == current_context['cluster']:
                current_cluster = cluster['cluster']
        for user in data['kubeconfig']['users']:
            if user['name'] == current_context['user']:
                current_user = user['user']

        manager = Manager.objects.create(
            name=data['name'],
            engine="kubernetes",
            metadata={
                'user': current_user,
                'cluster': current_cluster,
                'engine': "kubernetes",
                'scope': "global"
            })
        manager.save()
        if manager.client().check_status():
            manager.status = 'active'
        else:
            manager.status = 'error'
        manager.save()


class ManagerSyncForm(forms.Form):

    clean_resources = forms.BooleanField(label="Clean existing resources", initial=False, required=False, help_text='Will erase all resources and relationships for the given manager before resource synchronisation.')

    def __init__(self, *args, **kwargs):
        self.manager_name = kwargs.pop('manager_name')
        super().__init__(*args, **kwargs)
        detail_url = reverse('manager:manager_sync',
                             kwargs={'manager_name': self.manager_name})
        self.label = 'Sync {}'.format(self.manager_name)
        self.modal_class = 'modal-md'
        self.helper = FormHelper()
        self.helper.form_id = 'modal-form'
        self.helper.form_action = detail_url

        self.helper.layout = Layout(
            Div(
                Div(
                    Div('clean_resources', css_class='col-md-12'),
                    css_class='form-row'),
                css_class='modal-body',
            ),
            Div(
                Submit('submit', 'Synchronize', css_class='btn border-primary'),
                css_class='modal-footer',
            )
        )

    def handle(self):
        data = self.cleaned_data
        if data['clean_resources']:
            manager = Manager.objects.get(name=self.manager_name)
            Resource.objects.filter(manager=manager).delete()
            Relationship.objects.filter(manager=manager).delete()
        sync_manager_resources_task.apply_async((self.manager_name,))
