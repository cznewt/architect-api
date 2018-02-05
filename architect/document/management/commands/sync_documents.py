
from django.core.management.base import BaseCommand
from django.conf import settings
from architect.document.models import Document


class Command(BaseCommand):
    help = 'Synchronise Document objects'

    def handle(self, *args, **options):
        for engine_name, engine in settings.DOCUMENT_ENGINES.items():
            if Document.objects.filter(name=engine_name).count() == 0:
                document = Document(**{
                    'name': engine_name,
                    'metadata': engine
                })
                document.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        'Document "{}" resource created'.format(engine_name)))
            else:
                document = Document.objects.get(name=engine_name)
                document.metadata = engine
                document.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        'Document "{}" resource '
                        'updated'.format(engine_name)))
