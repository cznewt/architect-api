
from django.urls import path
from architect.monitor import views

app_name = 'monitor'
urlpatterns = [
    path('v1', views.MonitorListView.as_view(),
         name='monitor_list'),
    path('v1/<monitor_name>', views.MonitorDetailView.as_view(),
         name='monitor_detail'),
    path('v1/<monitor_name>/<widget_name>',
         views.WidgetDetailView.as_view(),
         name='widget_detail'),
    path('v1/<monitor_name>/<widget_name>/data.json',
         views.WidgetDetailJSONView.as_view(),
         name='widget_json_detail'),
]
