from django.urls import path
from . import views

app_name = 'manager'
urlpatterns = [
    path('v1', views.ManagerListView.as_view(),
         name='manager_list'),
    path('v1/<manager_name>', views.ManagerDetailView.as_view(),
         name='manager_detail'),
    path('v1/<manager_name>/sync', views.ManagerUpdateView.as_view(),
         name='manager_update'),
    path('v1/<manager_name>/<resource_name>',
         views.ResourceDetailView.as_view(),
         name='resource_detail'),
]
