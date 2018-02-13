
from django import forms
from django.contrib import admin
from django_select2.forms import ModelSelect2Widget
from architect.manager.models import Resource, Manager, Relationship
from architect.manager.tasks import get_manager_status_task, \
    sync_manager_resources_task


def get_manager_status(modeladmin, request, queryset):
    for manager in queryset:
        get_manager_status_task.apply_async((manager.name,))


get_manager_status.short_description = "Get status of selected managers"


def sync_manager_resources(modeladmin, request, queryset):
    for manager in queryset:
        sync_manager_resources_task.apply_async((manager.name,))


sync_manager_resources.short_description = "Synchronise resources of selected managers"


def clear_manager_resources(modeladmin, request, queryset):
    for manager in queryset:
        Resource.objects.filter(manager=manager).delete()


clear_manager_resources.short_description = "Clear resources of selected managers"


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ('name', 'engine', 'status', 'conn_detail')
    list_filter = ('engine', 'status')
    actions = [
        get_manager_status,
        sync_manager_resources,
        clear_manager_resources
    ]


class RelationWidget(ModelSelect2Widget):
    model = Relationship

    def label_from_instance(obj):
        return str(obj.name)


class SourceRelationshipForm(forms.ModelForm):
    class Meta:
        model = Relationship
        fields = (
            'target',
            'kind',
            'size',
            'status',
        )
        widgets = {
            'target': RelationWidget,
        }


class TargetRelationshipForm(forms.ModelForm):
    class Meta:
        model = Relationship
        fields = (
            'source',
            'kind',
            'size',
            'status',
        )
        widgets = {
            'source': RelationWidget,
        }


class SourceRelationshipInline(admin.TabularInline):
    model = Relationship
    form = SourceRelationshipForm
    fk_name = 'source'
    extra = 1


class TargetRelationshipInline(admin.TabularInline):
    model = Relationship
    form = TargetRelationshipForm
    fk_name = 'target'
    extra = 1


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'uid', 'manager', 'kind', 'status')
    list_filter = ('manager', 'status', 'kind')
    search_fields = ['uid', 'name']
#    inlines = [
#        SourceRelationshipInline,
#        TargetRelationshipInline,
#    ]


@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager', 'kind', 'source', 'target')
    list_filter = ('manager', 'status', 'kind')
