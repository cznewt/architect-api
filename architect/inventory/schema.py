import graphene
from architect.inventory.models import Inventory
from graphene import Node
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType


class InventoryNode(DjangoObjectType):

    class Meta:
        model = Inventory
        interfaces = (Node, )
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'engine': ['exact', 'icontains', 'istartswith'],
            'description': ['exact', 'icontains', 'istartswith'],
            'status': ['exact', 'icontains', 'istartswith'],
        }


class Query(graphene.ObjectType):
    inventories = DjangoFilterConnectionField(InventoryNode)


schema = graphene.Schema(query=Query)
