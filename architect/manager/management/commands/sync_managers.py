
from django.core.management.base import BaseCommand
from django.conf import settings
from architect.manager.models import Manager


class Command(BaseCommand):
    help = 'Synchronise Manager objects'

    def handle(self, *args, **options):
        for engine_name, engine in settings.MANAGER_ENGINES.items():
            if Manager.objects.filter(name=engine_name).count() == 0:
                engine_engine = engine.pop('engine')
                manager = Manager(**{
                    'engine': engine_engine,
                    'name': engine_name,
                    'metadata': engine
                })
                manager.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        'Manager "{}" resource created'.format(engine_name)))
            else:
                manager = Manager.objects.get(name=engine_name)
                manager.metadata = engine
                manager.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        'Manager "{}" resource '
                        'updated'.format(engine_name)))
