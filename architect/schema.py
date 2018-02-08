import architect.document.schema
import architect.inventory.schema
import architect.manager.schema
import architect.monitor.schema
import graphene
from graphene_django.debug import DjangoDebug


class Query(architect.document.schema.schema.Query,
            architect.manager.schema.schema.Query,
            architect.inventory.schema.schema.Query,
            architect.monitor.schema.schema.Query,
            graphene.ObjectType):
    debug = graphene.Field(DjangoDebug, name='__debug')


schema = graphene.Schema(query=Query)
