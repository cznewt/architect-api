from django.core.management.base import BaseCommand
from django.conf import settings
from architect.manager.models import Resource


class Command(BaseCommand):
    help = 'Synchronise core Manager objects'

    def handle(self, *args, **options):
        for engine_name, engine in settings.MANAGER_ENGINES.items():
            resources = Resource.objects.all()
            resource_count = resources.count()
            resources.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    'Deleted {} resources'.format(resource_count)))
