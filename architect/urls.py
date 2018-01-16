"""
Architect service URL configuration
"""
from django.views import generic
from django.conf.urls import url, include
from material.frontend import urls as frontend_urls

urlpatterns = [
    url(r'^$',
        generic.RedirectView.as_view(url='/inventory/v1',
                                     permanent=False)),
    url(r'^doc/',
        include('django.contrib.admindocs.urls')),
    url(r'^inventory/',
        include('architect.inventory.urls', namespace='inventory')),
    url(r'^manager/',
        include('architect.manager.urls', namespace='manager')),
    url(r'^monitor/',
        include('architect.monitor.urls', namespace='monitor')),
    url(r'^salt/',
        include('architect.manager.engine.saltstack.urls')),
    url(r'^ansible/',
        include('architect.manager.engine.ansible.urls')),
    url(r'',
        include(frontend_urls)),
]
