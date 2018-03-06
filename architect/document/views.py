# -*- coding: utf-8 -*-

from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Document


class DocumentListView(LoginRequiredMixin, TemplateView):
    template_name = "document/document_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_list'] = Document.objects.order_by('name')
        return context


class DocumentDetailView(LoginRequiredMixin, TemplateView):
    template_name = "document/document_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document = Document.objects.get(name=kwargs.get('document_name'))
        context['document'] = document
        return context
