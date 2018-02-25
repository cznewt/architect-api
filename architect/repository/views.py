# -*- coding: utf-8 -*-

from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.base import RedirectView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Repository
from .forms import RepositoryCreateForm, RepositoryDeleteForm


class RepositoryListView(TemplateView):

    template_name = "repository/repository_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['repository_list'] = Repository.objects.order_by('name')
        return context


class RepositoryCheckView(RedirectView):

    permanent = False
    query_string = True
    pattern_name = 'repository:repository_list'

    def get_redirect_url(self, *args, **kwargs):
        repositories = Repository.objects.all()
        messages.add_message(self.request,
                             messages.SUCCESS,
                             'Finished syncing of repositories.')
        return super().get_redirect_url(*args, **kwargs)


class RepositorySyncView(RedirectView):

    permanent = False
    pattern_name = 'repository:repository_detail'

    def get_redirect_url(self, *args, **kwargs):
        return super().get_redirect_url(*args, **kwargs)


class RepositoryDetailView(TemplateView):

    template_name = "repository/repository_detail.html"

    def get_context_data(self, **kwargs):
        repository = Repository.objects.get(name=kwargs.get('repository_name'))
        context = super().get_context_data(**kwargs)
        context['repository'] = repository


class RepositoryCreateView(FormView):

    template_name = "base_form.html"
    form_class = RepositoryCreateForm
    success_url = '/success'
    initial = {
        'classes_dir': '/srv/salt/reclass/classes',
        'nodes_dir': '/srv/salt/reclass/nodes',
    }

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


class RepositoryDeleteView(FormView):

    template_name = "base_form.html"
    form_class = RepositoryDeleteForm
    success_url = '/repository/v1/success'

    def get_success_url(self):
        return reverse('repository:repository_list')

    def get_form_kwargs(self):
        repository_name = self.kwargs.get('repository_name')
        kwargs = super(RepositoryDeleteView, self).get_form_kwargs()
        kwargs.update({'initial': {'repository_name': repository_name}})
        return kwargs

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


