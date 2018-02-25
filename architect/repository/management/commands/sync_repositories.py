
from django.core.management.base import BaseCommand
from django.conf import settings
from architect.repository.models import Repository


class Command(BaseCommand):
    help = 'Synchronise Repository objects'

    def handle(self, *args, **options):
        for engine_name, engine in settings.REPOSITORY_ENGINES.items():
            if Repository.objects.filter(name=engine_name).count() == 0:
                engine_kind = engine.pop('engine')
                repository = Repository(**{
                    'name': engine_name,
                    'engine': engine_kind,
                    'metadata': engine
                })
                repository.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        'Repository "{}" resource '
                        'created'.format(engine_name)))
            else:
                repository = Repository.objects.get(name=engine_name)
                repository.metadata = engine
                repository.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        'Repository "{}" resource '
                        'updated'.format(engine_name)))
