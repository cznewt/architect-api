import graphene
from architect.monitor.models import Monitor
from graphene import Node
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType


class MonitorNode(DjangoObjectType):

    class Meta:
        model = Monitor
        interfaces = (Node, )
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'engine': ['exact', 'icontains', 'istartswith'],
            'description': ['exact', 'icontains', 'istartswith'],
            'status': ['exact', 'icontains', 'istartswith'],
        }


class Query(graphene.ObjectType):
    monitors = DjangoFilterConnectionField(MonitorNode)


schema = graphene.Schema(query=Query)
