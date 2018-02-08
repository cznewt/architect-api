import graphene
from architect.document.models import Document
from graphene import Node
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType


class DocumentNode(DjangoObjectType):

    widgets = graphene.List(graphene.types.json.JSONString)

    class Meta:
        model = Document
        interfaces = (Node, )
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'engine': ['exact', 'icontains', 'istartswith'],
            'description': ['exact', 'icontains', 'istartswith'],
            'status': ['exact', 'icontains', 'istartswith'],
        }


class Query(graphene.ObjectType):
    documents = DjangoFilterConnectionField(DocumentNode)


schema = graphene.Schema(query=Query)
