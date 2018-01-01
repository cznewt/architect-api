from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^v1/enc/(?P<master_id>[\w\-\.]+)$',
        views.GetInventoryView.as_view(),
        name='salt_enc_inventory'),
    url(r'^v1/enc/(?P<master_id>[\w\-\.]+)/(?P<minion_id>[\w\-\.]+)/pillar$',
        views.GetNodePillarView.as_view(),
        name='salt_enc_pillar'),
    url(r'^v1/enc/(?P<master_id>[\w\-\.]+)/(?P<minion_id>[\w\-\.]+)/top$',
        views.GetNodeTopView.as_view(),
        name='salt_enc_top'),
    url(r'^v1/event/(?P<master_id>[\w\-\.]+)$',
        views.ProcessEventView.as_view(),
        name='salt_event'),
    url(r'^v1/grain/(?P<master_id>[\w\-\.]+)$',
        views.ProcessGrainView.as_view(),
        name='salt_grain'),
    url(r'^v1/lowstate/(?P<master_id>[\w\-\.]+)$',
        views.ProcessLowstateView.as_view(),
        name='salt_lowstate'),
    url(r'^v1/pillar/(?P<master_id>[\w\-\.]+)$',
        views.ProcessPillarView.as_view(),
        name='salt_pillar'),
]
