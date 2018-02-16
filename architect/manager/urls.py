from django.urls import path
from . import views

app_name = 'manager'
urlpatterns = [
    path('v1', views.ManagerListView.as_view(),
         name='manager_list'),
    path('v1/manager-check',
         views.ManagerCheckView.as_view(),
         name='manager_check'),
    path('v1/manager-create/data.json',
         views.ManagerCreateJSONView.as_view(),
         name='manager_json_create'),
    path('v1/<manager_name>',
         views.ManagerDetailView.as_view(),
         name='manager_detail'),
    path('v1/<manager_name>/sync',
         views.ManagerSyncView.as_view(),
         name='manager_sync'),
    path('v1/<manager_name>/query/<query_name>',
         views.ManagerQueryJSONView.as_view(),
         name='manager_query'),
    path('v1/<manager_name>/action/<resource_kind>/<manager_action>',
         views.ManagerActionView.as_view(),
         name='manager_action'),
    path('v1/<manager_name>/resource/<resource_uid>',
         views.ResourceDetailView.as_view(),
         name='resource_detail'),
    path('v1/<manager_name>/resource/<resource_uid>/<resource_action>',
         views.ResourceActionView.as_view(),
         name='resource_action'),
]
