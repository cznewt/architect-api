from django.urls import path
from . import views

app_name = 'repository'
urlpatterns = [
    path('v1',
         views.RepositoryListView.as_view(),
         name='repository_list'),
    path('v1/repository-create',
         views.RepositoryCreateView.as_view(),
         name='repository_create'),
    path('v1/repository-check',
         views.RepositoryCheckView.as_view(),
         name='repository_check'),
    path('v1/<repository_name>',
         views.RepositoryDetailView.as_view(),
         name='repository_detail'),
    path('v1/<repository_name>/sync',
         views.RepositorySyncView.as_view(),
         name='repository_sync'),
    path('v1/<repository_name>/delete',
         views.RepositoryDeleteView.as_view(),
         name='repository_delete'),
]
