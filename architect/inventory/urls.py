from django.conf.urls import url
from . import views

app_name = 'inventory'
urlpatterns = [
    url(r'^v1$',
        views.InventoryListView.as_view(),
        name='inventory_list'),
    url(r'^v1/(?P<inventory_name>[\w\.]+)$',
        views.InventoryDetailView.as_view(),
        name='inventory_detail'),
    url(r'^v1/(?P<inventory_name>[\w\.]+)/(?P<host_name>[\w\.]+)$',
        views.HostDetailView.as_view(),
        name='host_detail'),
]
