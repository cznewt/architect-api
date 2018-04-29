from django.urls import path
from . import views

app_name = 'repository'
urlpatterns = [
    path('v1',
         views.RepositoryListView.as_view(),
         name='repository_list'),
    path('v1/<repository_name>',
         views.RepositoryDetailView.as_view(),
         name='repository_detail'),
    path('v1/<repository_name>/image-create',
         views.ImageCreateView.as_view(),
         name='image_create'),
    path('v1/<repository_name>/image/<image_name>',
         views.ImageDetailView.as_view(),
         name='image_detail'),
    path('v1/<repository_name>/image/<image_name>/download',
         views.ImageDownloadView.as_view(),
         name='image_download'),
    path('v1/<repository_name>/image/<image_name>/delete',
         views.ImageDeleteView.as_view(),
         name='image_delete'),
]
