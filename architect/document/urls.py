
from django.urls import path
from architect.document import views

app_name = 'document'
urlpatterns = [
    path('v1', views.DocumentListView.as_view(),
         name='document_list'),
    path('v1/<document_name>', views.DocumentDetailView.as_view(),
         name='document_detail'),
]
