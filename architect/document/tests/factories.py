import factory


class DocumentFactory(factory.django.DjangoModelFactory):
    name = 'document-1'
    description = 'Long description'

    class Meta:
        model = 'document.Document'
        django_get_or_create = ('name', )
