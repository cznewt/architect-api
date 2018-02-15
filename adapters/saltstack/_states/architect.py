
def node_classified(name, data={}):
    '''
    Classify node, create inventory level overrides and/or node models

    :param name: Node FQDN
    :param data: Node parameters passed to the classifier

    '''
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': 'Node "{0}" is already classified.'.format(name)}

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'Node "{0}" would be classified'.format(name)
        return ret

    classification = __salt__['architect.node_classify'](name, data)
    ret['comment'] = 'Node "{0}" has been classified'.format(name)
    ret['changes']['Node'] = classification

    return ret
