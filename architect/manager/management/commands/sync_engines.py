from django.core.management.base import BaseCommand
from django.conf import settings
from architect.inventory.models import registry

SaltMasterNode = registry.get_type('salt_master')


class Command(BaseCommand):
    help = 'Synchronise core Manager objects'

    def handle(self, *args, **options):
        for engine_name, engine in settings.MANAGER_ENGINES.items():
            if engine['engine'] == 'saltstack':
                resource_meta = {
                    'uid': engine_name,
                    'kind': 'salt_master',
                    'name': engine_name,
                    'metadata': engine
                }
                SaltMasterNode.create_or_update(resource_meta)
                self.stdout.write(self.style.SUCCESS('Salt Master "%s" resource created/updated.' % engine_name))
