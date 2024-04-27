from ckanext.workflow.model import WorkflowRequest
from ckan.plugins import toolkit

_ = toolkit._

unicode_only = toolkit.get_validator("unicode_only")
one_of = toolkit.get_validator("one_of")


def request_id_does_not_exist(request_id):
    '''
        Return the given request_id if such a WorkflowRequest exists.
        :raises: toolkit.Invalid if no request can be found with the given request_id
    '''    
    result = WorkflowRequest.get(request_id)
    if result:
        raise toolkit.Invalid(_('Request id already exists'))
    return request_id


def organization_id_exists(organization_id, context):
    '''
        Return the given organization_id if such a Group exists and that Group is an organization.
        :raises: toolkit.Invalid if no request can be found with the given organization_id
    '''    
    model = context['model']
    session = context['session']

    result = session.query(model.Group).get(organization_id)
    if not result or result.is_organization:
        raise toolkit.Invalid('%s: %s' % (_('Not found'), _('Organization')))
    return organization_id


def request_state_exists(request_state):
    return request_state


def request_approval_validator(key, converted_data, errors, context):
    pass


def is_function(value):
    if not callable(value) and not hasattr(value, "__call__"):
        raise toolkit.Invalid(_('Request id already exists'))
    return value


def is_function_with_parameters(varnames):
    def callable(value):
        value = is_function(value)
        func_varnames = set(value.__code__.co_varnames[:value.__code__.co_argcount])
        if not func_varnames == set(varnames):
            raise toolkit.Invalid(_('Request id already exists'))
        return value
    return callable
    

def is_text_function(value):
    unicode_only(is_function(value)())
    return value


def list_one_of(list_of_value):

    def callable(value):
        if not isinstance(value, list):
            value = [value]
        for v in value:
            one_of(list_of_value)(v)
        return value
    return callable


def one_of_validators(list_of_validators):
    def callable(value):
        for validator in list_of_validators:
            try:
                validator(value)
                return value
            except toolkit.Invalid as e:
                pass
        raise toolkit.Invalid(_('Value must be one of {}'.format(list_of_validators)))
    return callable


def list_one_of_validators(list_of_validators):
    def callable(value):
        if not isinstance(value, list):
            value = [value]
        for v in value:
            one_of_validators(list_of_validators)(v)
        return value
    return callable
