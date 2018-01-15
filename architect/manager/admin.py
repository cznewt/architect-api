
from django.contrib import admin
from architect.manager.models import Resource, Manager, Relationship
from architect.manager.tasks import get_manager_status_task


def get_manager_status(modeladmin, request, queryset):
    for manager in queryset:
        get_manager_status_task.apply_async((manager.name,))


get_manager_status.short_description = "Update status of selected managers"


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ('name', 'engine', 'status', 'url')
    list_filter = ('engine', 'status')
    actions = [get_manager_status]


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager', 'kind', 'status')
    list_filter = ('manager', 'status', 'kind')
    search_fields = ['uid', 'name']


@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager', 'kind', 'source', 'target')
    list_filter = ('manager', 'status', 'kind')
