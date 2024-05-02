from typing import Dict, Callable
from ckanext.workflow.model import WorkflowRequest
from ckan.plugins import toolkit
import ckanext.workflow.constants as workflow_constants

# noinspection PyProtectedMember
_ = toolkit._

unicode_only = toolkit.get_validator("unicode_only")
one_of = toolkit.get_validator("one_of")


def request_id_does_not_exist(request_id: str) -> str:
    """
        Returns:
            the given value if a WorkflowRequest identified by the request_id can be found
        Raises:
            Invalid if not found
    """
    result = WorkflowRequest.get(request_id)
    if result:
        raise toolkit.Invalid(_('Request id already exists'))
    return request_id


def organization_id_exists(organization_id: str, context: Dict) -> str:
    """
        Raises Invalid if an organization identified by the id cannot be found
    """
    model = context['model']
    session = context['session']

    result = session.query(model.Group).get(organization_id)

    if not result or not result.is_organization:
        raise toolkit.Invalid('%s: %s' % (_('Not found'), _('Organization')))
    return organization_id


def state_exists(state):
    if state not in workflow_constants.WORKFLOW.get_states():
        raise toolkit.Invalid('%s: %s' % (_('Not found'), _('WorkflowState')))
    return state


def request_approval_validator(key, converted_data, errors, context):
    pass


def is_function(value: Callable):
    """
        Raises Invalid if the given value is not a function (can't be called)
    """
    if not callable(value) and not hasattr(value, "__call__"):
        raise toolkit.Invalid(_('Value must be a function'))
    return value


def is_function_with_parameters(parameters):
    """
        Returns a 
    """    
    
    '''Raises Invalid if the given value is not a function (can't be called)'''   
    def _is_function_with_parameters(value):
        value = is_function(value)
        # noinspection PyUnresolvedReferences
        func_parameters = set(value.__code__.co_varnames[:value.__code__.co_argcount])
        if not func_parameters == set(parameters):
            raise toolkit.Invalid(_('is_function_with_parameters'))
        return value
    return _is_function_with_parameters
    

def is_text_function(text_function: Callable[[], str]) -> Callable[[], str]:
    """_summary_

    Args:
        text_function (Callable[[], str]): _description_

    Returns:
        Callable[[], str]: _description_
    """
    unicode_only(is_function(text_function)())
    return text_function


def list_one_of(list_of_value):

    def _list_one_of(value):
        if not isinstance(value, list):
            value = [value]
        for v in value:
            one_of(list_of_value)(v)
        return value
    return _list_one_of


def one_of_validators(list_of_validators):
    def _one_of_validators(value):
        for validator in list_of_validators:
            try:
                validator(value)
                return value
            except toolkit.Invalid as e:
                pass
        raise toolkit.Invalid(_('Value must be one of {}'.format(list_of_validators)))
    return _one_of_validators


def list_one_of_validators(list_of_validators):
    def _list_one_of_validators(value):
        if not isinstance(value, list):
            value = [value]
        for v in value:
            one_of_validators(list_of_validators)(v)
        return value
    return _list_one_of_validators
