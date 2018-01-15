from django.conf.urls import url
from . import views

urlpatterns = [
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
