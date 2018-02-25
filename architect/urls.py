"""
Architect service URL configuration
"""
from django.contrib import admin
from django.urls import path
from django.views import generic
from django.conf.urls import include
from graphene_django.views import GraphQLView
from architect.views import FormSuccessView

urlpatterns = [
    path('',
         generic.RedirectView.as_view(url='/manager/v1')),
    path('admin/', admin.site.urls),
    path('doc/',
         include('django.contrib.admindocs.urls')),
    path('api-auth/',
         include('rest_framework.urls')),
    path('select2/',
         include('django_select2.urls')),
    path('document/',
         include('architect.document.urls',
                 namespace='document')),
    path('inventory/',
         include('architect.inventory.urls',
                 namespace='inventory')),
    path('manager/',
         include('architect.manager.urls',
                 namespace='manager')),
    path('monitor/',
         include('architect.monitor.urls',
                 namespace='monitor')),
    path('repository/',
         include('architect.repository.urls',
                 namespace='repository')),
    path('salt/',
         include('architect.manager.engine.saltstack.urls')),
    path('graphql/',
         GraphQLView.as_view(graphiql=True)),
    path('success',
         FormSuccessView.as_view(),
         name='form_success'),
]
