from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^v1/event/(?P<master_id>[\w\-\.]+)$',
        views.ProcessEventView.as_view(),
        name='salt_event'),
    url(r'^v1/minion/(?P<master_id>[\w\-\.]+)$',
        views.ProcessMinionView.as_view(),
        name='salt_minion'),
    url(r'^v1/class/(?P<master_id>[\w\-\.]+)$',
        views.ProcessClassView.as_view(),
        name='salt_class'),
]
