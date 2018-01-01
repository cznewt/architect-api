from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^v1/enc/(?P<inventory_id>[\w\.]+)$',
        views.GetInventoryView.as_view(),
        name='ansible_enc_inventory'),
    url(r'^v1/enc/(?P<inventory_id>[\w\.]+)/(?P<host_id>[\w\.]+)$',
        views.GetHostDataView.as_view(),
        name='ansible_enc_host'),
]
