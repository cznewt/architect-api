import graphene
from architect.manager.models import Manager, Relationship, Resource
from graphene import Node
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType


class ManagerNode(DjangoObjectType):

    class Meta:
        model = Manager
        interfaces = (Node, )
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'engine': ['exact', 'icontains', 'istartswith'],
            'description': ['exact', 'icontains', 'istartswith'],
            'status': ['exact', 'icontains', 'istartswith'],
        }


class RelationshipNode(DjangoObjectType):

    class Meta:
        model = Relationship
        interfaces = (Node, )
        filter_fields = ['id']


class ResourceNode(DjangoObjectType):

    class Meta:
        model = Resource
        interfaces = (Node, )
        filter_fields = ['id']


class Query(graphene.ObjectType):
    managers = DjangoFilterConnectionField(ManagerNode)
    relationships = DjangoFilterConnectionField(RelationshipNode)
    resources = DjangoFilterConnectionField(ResourceNode)


schema = graphene.Schema(query=Query)
