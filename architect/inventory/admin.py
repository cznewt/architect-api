
from django.contrib import admin
from architect.inventory.models import Inventory, Resource


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'engine', 'status')
    list_filter = ('status', 'engine')


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'uid', 'inventory', 'kind', 'status')
    list_filter = ('inventory', 'status', 'kind')
    search_fields = ['uid', 'name']
