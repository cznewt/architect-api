
from django.core.management.base import BaseCommand
from django.conf import settings
from architect.inventory.models import Inventory


class Command(BaseCommand):
    help = 'Synchronise Inventory objects'

    def handle(self, *args, **options):
        for engine_name, engine in settings.INVENTORY_ENGINES.items():
            if Inventory.objects.filter(name=engine_name).count() == 0:
                engine_engine = engine.pop('engine')
                inventory = Inventory(**{
                    'engine': engine_engine,
                    'name': engine_name,
                    'metadata': engine
                })
                inventory.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        'Inventory "{}" resource created'.format(engine_name)))
            else:
                inventory = Inventory.objects.get(name=engine_name)
                inventory.metadata = engine
                inventory.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        'Inventory "{}" resource '
                        'updated'.format(engine_name)))
