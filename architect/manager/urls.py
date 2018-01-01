from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^v1$',
        views.ManagerListView.as_view(),
        name='manager_list'),
    url(r'^v1/(?P<manager_name>[\w\-\.]+)$',
        views.ManagerDetailView.as_view(),
        name='manager_detail'),
    url(r'^v1/(?P<manager_name>[\w\-\.]+)/(?P<host_name>[\w\-\.]+)$',
        views.HostDetailView.as_view(),
        name='host_detail'),
    url(r'^v1/(?P<manager_name>[\w\-\.]+)/(?P<host_name>[\w\-\.]+)/(?P<service_name>[\w\-\.]+)$',
        views.ServiceDetailView.as_view(),
        name='service_detail'),
]
