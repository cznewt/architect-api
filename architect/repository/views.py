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
from .models import Repository, Resource
from .forms import ImageCreateForm, ImageDeleteForm


class RepositoryListView(TemplateView):

    template_name = "repository/repository_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['repository_list'] = Repository.objects.order_by('name')
        return context


class RepositoryDetailView(TemplateView):

    template_name = "repository/repository_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['repository'] = Repository.objects.get(name=kwargs.get('repository_name'))
        return context


class ImageCreateView(FormView):

    template_name = "base_form.html"
    form_class = ImageCreateForm
    success_url = '/success'
    initial = {}

    def get_form_kwargs(self):
        repository_name = self.kwargs.get('repository_name')
        kwargs = super(ImageCreateView, self).get_form_kwargs()
        kwargs.update({'initial': {'repository_name': repository_name}})
        return kwargs

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


class ImageDeleteView(FormView):

    template_name = "base_form.html"
    form_class = ImageDeleteForm
    success_url = '/success'

    def get_form_kwargs(self):
        kwargs = super(ImageDeleteView, self).get_form_kwargs()
        kwargs.update(self.kwargs)
        return kwargs

    def form_valid(self, form):
        form.handle()
        return super().form_valid(form)


