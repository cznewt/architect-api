
from django.contrib import admin
from architect.repository.models import Repository, Resource


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'engine', 'status')
    list_filter = ('status', 'engine')


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'uid', 'repository', 'kind', 'status')
    list_filter = ('repository', 'status', 'kind')
    search_fields = ['uid', 'name']
