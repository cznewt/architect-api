
from django.urls import path
from architect.monitor import views

app_name = 'monitor'
urlpatterns = [
    path('v1', views.MonitorListView.as_view(),
         name='monitor_list'),
    path('v1/<monitor_name>', views.MonitorDetailView.as_view(),
         name='monitor_detail'),
    path('v1/<manager_name>/query/<query_name>',
         views.MonitorQueryJSONView.as_view(),
         name='manager_query'),
]
