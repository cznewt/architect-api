from django.urls import path
from . import views

app_name = 'inventory'
urlpatterns = [
    path('v1',
         views.InventoryListView.as_view(),
         name='inventory_list'),
    path('v1/<inventory_name>',
         views.InventoryDetailView.as_view(),
         name='inventory_detail'),
    path('v1/<inventory_name>/data.json',
         views.InventoryDetailJSONView.as_view(),
         name='inventory_json_detail'),
    path('v1/<inventory_name>/<resource_name>',
         views.ResourceDetailView.as_view(),
         name='resource_detail'),
    path('v1/<inventory_name>/<resource_name>/data.json',
         views.ResourceDetailJSONView.as_view(),
         name='resource_json_detail'),
]
