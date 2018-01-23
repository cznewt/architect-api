"""
Architect service URL configuration
"""

from django.urls import path
from django.views import generic
from django.conf.urls import include
from material.frontend import urls as frontend_urls

urlpatterns = [
    path('',
         generic.RedirectView.as_view(url='/manager/v1')),
    path('doc/',
         include('django.contrib.admindocs.urls')),
    path('select2/',
         include('django_select2.urls')),
    path('inventory/',
         include('architect.inventory.urls', namespace='inventory')),
    path('manager/',
         include('architect.manager.urls', namespace='manager')),
    path('monitor/',
         include('architect.monitor.urls', namespace='monitor')),
    path('salt/',
         include('architect.manager.engine.saltstack.urls')),
    path('workflow/', include(frontend_urls)),
]
