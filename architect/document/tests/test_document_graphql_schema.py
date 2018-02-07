
from architect.document.tests.factories import DocumentFactory
from architect.schema import schema
from test_plus.test import TestCase


class TestDocumentSchema(TestCase):

    document_factory = DocumentFactory

    def setUp(self):
        self.document = self.document_factory.create()

    def test__str__(self):
        self.assertEqual(
            self.document.__str__(),
            'document-1'
        )

    def test_query(self):
        query = '''
            query {
              documents {
                edges {
                    node {
                        name
                    }
                }
              }
            }
        '''
        result = schema.execute(query)
        self.assertEqual(result.errors, None)
        self.assertEqual(
            result.data,
            {'documents': {'edges': [{'node': {'name': 'document-1'}}]}}
        )
