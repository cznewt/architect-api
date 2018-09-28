
from django.urls import path
from architect.monitor import views

app_name = 'monitor'
urlpatterns = [
    path('v1', views.MonitorListView.as_view(),
         name='monitor_list'),
    path('v1/monitor-check',
         views.MonitorCheckView.as_view(),
         name='monitor_check'),
    path('v1/<monitor_name>', views.MonitorDetailView.as_view(),
         name='monitor_detail'),
    path('v1/<monitor_name>/sync',
         views.MonitorSyncView.as_view(),
         name='monitor_sync'),
    path('v1/<monitor_name>/graph/<query_name>/<viz_name>',
         views.MonitorGraphView.as_view(),
         name='monitor_graph'),
    path('v1/<monitor_name>/resource/<resource_uid>',
         views.ResourceDetailView.as_view(),
         name='resource_detail'),
    path('v1/<manager_name>/query/<query_name>/<query_type>',
         views.MonitorQueryJSONView.as_view(),
         name='manager_query'),
]
