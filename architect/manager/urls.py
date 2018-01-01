from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^v1$',
        views.ManagerListView.as_view(),
        name='manager_list'),
    url(r'^v1/(?P<name>[\w\.]+)$',
        views.ManagerDetailView.as_view(),
        name='manager_detail'),
]
