from neomodel import StructuredNode, StringProperty, \
    IntegerProperty, JSONProperty
from neomodel.match import OUTGOING, INCOMING, EITHER
from neomodel.relationship_manager import RelationshipManager
from neomodel.relationship import StructuredRel
from architect import utils

registry = utils.ClassRegistry()

class ResourceRel(StructuredRel):
    size = IntegerProperty(default=1)
    status = StringProperty(default='unknown')


class RelationshipDefinition(object):
    def __init__(self, relation_type, cls_name, direction,
                 manager=RelationshipManager,
                 model=None):
        self._raw_class = cls_name
        self.manager = manager
        self.definition = {}
        self.definition['relation_type'] = relation_type
        self.definition['direction'] = direction
        self.definition['model'] = model

    def _lookup_node_class(self):
        if not isinstance(self._raw_class, str):
            self.definition['node_class'] = self._raw_class
        else:
            name = self._raw_class
            self.definition['node_class'] = registry.get_type(name)

    def build_manager(self, source, name):
        self._lookup_node_class()
        return self.manager(source, name, self.definition)


class ZeroOrMore(RelationshipManager):
    description = "zero or more relationships"


def _relate(cls_name, direction, rel_type, cardinality=None, model=None):

    if model and not issubclass(model, (StructuredRel,)):
        raise ValueError('model must be a StructuredRel')
    return RelationshipDefinition(rel_type,
                                  cls_name,
                                  direction,
                                  cardinality,
                                  model)


def RelationshipTo(cls_name, rel_type, cardinality=ZeroOrMore, model=None):
    return _relate(cls_name, OUTGOING, rel_type, cardinality, model)


def RelationshipFrom(cls_name, rel_type, cardinality=ZeroOrMore, model=None):
    return _relate(cls_name, INCOMING, rel_type, cardinality, model)


def Relationship(cls_name, rel_type, cardinality=ZeroOrMore, model=None):
    return _relate(cls_name, EITHER, rel_type, cardinality, model)


def create_relations(relation_types):
    for relation_name, relation in relation_types.items():
        registry.add(type(
            relation_name,
            (ResourceRel,),
            relation.get('model', {})))


def create_resources(resource_types):
    for resource_name, resource in resource_types.items():
        fields = {
            'uid': StringProperty(unique_index=True),
            'name': StringProperty(required=True),
            'kind': StringProperty(required=True),
            'status': StringProperty(default='Unknown'),
            'metadata': JSONProperty(),
        }
        for field_name, field in resource.get('model', {}).items():
            cls_name = field.pop("type")
            target_cls = field.pop('target')
            model_name = field.pop('model')
            field['model'] = registry.get_type(model_name)
            fields[field_name] = globals().get(utils.to_camel_case(cls_name))(target_cls, model_name, **field)
        registry.add(type(resource_name,
                     (StructuredNode,), fields))


salt_schema = utils.get_resource_schema('saltstack')

create_relations(salt_schema['relation'])
create_resources(salt_schema['resource'])
