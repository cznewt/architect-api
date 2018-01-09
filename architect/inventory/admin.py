
from django.contrib import admin
from architect.inventory.models import Inventory


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'engine', 'status')
