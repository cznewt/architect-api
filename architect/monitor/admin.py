
from django.contrib import admin
from architect.monitor.models import Monitor, Resource, Relationship


def clear_monitor_resources(modeladmin, request, queryset):
    for monitor in queryset:
        Resource.objects.filter(monitor=monitor).delete()
        Relationship.objects.filter(monitor=monitor).delete()


clear_monitor_resources.short_description = "Clear resources of selected monitors"


@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'engine', 'status')
    list_filter = ('status',)
    actions = [
        clear_monitor_resources
    ]


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'uid', 'monitor', 'kind')
    list_filter = ('monitor', 'kind')
    search_fields = ['uid', 'name']


@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    list_display = ('source', 'target', 'monitor', 'kind')
    list_filter = ('monitor', 'kind')
