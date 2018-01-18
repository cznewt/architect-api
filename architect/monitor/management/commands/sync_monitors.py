from django.core.management.base import BaseCommand
from django.conf import settings
from architect.monitor.models import Monitor


class Command(BaseCommand):
    help = 'Synchronise core Monitor objects'

    def handle(self, *args, **options):
        for engine_name, engine in settings.MONITOR_ENGINES.items():
            if Monitor.objects.filter(name=engine_name).count() == 0:
                monitor = Monitor(**{
                    'name': engine_name,
                    'metadata': engine
                })
                monitor.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        'Monitor "{}" resource created'.format(engine_name)))
            else:
                monitor = Monitor.objects.get(name=engine_name)
                monitor.metadata = engine
                monitor.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        'Monitor "{}" resource '
                        'updated'.format(engine_name)))
