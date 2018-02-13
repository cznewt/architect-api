
from django import forms
from django.urls import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit
from .tasks import process_resource_action_task
from .models import Resource


class ManagerActionForm(forms.Form):

    def __init__(self, *args, **kwargs):
        parameters = kwargs.pop('params')
        manager_name = kwargs.pop('manager_name')
        resource_kind = kwargs.pop('resource_kind')
        resource_action = kwargs.pop('resource_action')
        super(ResourceActionForm, self).__init__(*args, **kwargs)
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
        super(ResourceActionForm, self).__init__(*args, **kwargs)

        action_url = reverse('manager:resource_action',
                             kwargs={'manager_name': self.manager.name,
                                     'resource_uid': self.resource.uid,
                                     'resource_action': self.action})
        layout_fields = []

        for param_name, param_field in parameters.items():
            self.fields[param_name] = param_field
            layout_fields.append(param_name)

        self.label = self.manager.client()._schema['resource'][self.resource.kind]['workflow'][self.action]['name']
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

    def handle(self):
        data = self.clean()
        process_resource_action_task.apply_async((self.manager.name,
                                                  self.resource.uid,
                                                  self.action,
                                                  data))
