
from django.contrib import admin
from architect.monitor.models import Monitor


@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    list_filter = ('status',)
