from typing import Dict, Callable

from ckanext.workflow import common
from ckanext.workflow.model import WorkflowPackageRequest
from ckan.plugins import toolkit
# logging
import logging
import re

log = logging.getLogger(__name__)

# noinspection PyProtectedMember
_ = toolkit._

unicode_only = toolkit.get_validator("unicode_only")
one_of = toolkit.get_validator("one_of")


def is_action(action_name):
    """
        Returns:
            the given value if an action identified by the action_name can be found
        Raises:
            Invalid if not found
    """
    try:
        common.get_action(action_name)
        return action_name
    except KeyError:
        raise toolkit.Invalid(_("Given action '{}' does not exist".format(action_name)))


def request_id_does_not_exist(request_id: str) -> str:
    """
        Returns:
            the given value if a WorkflowPackageRequest identified by the request_id can be found
        Raises:
            Invalid if not found
    """
    result = WorkflowPackageRequest.get(request_id)
    if result:
        raise toolkit.Invalid(_('Request id already exists'))
    return request_id


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


def is_css_hex_color(value):

    # start with all the 'simple' checks based on the allowed forms '#xxx' or '#yyyyyy'
    correct = bool(value) and value.startswith('#') and len(value) in [4, 7]
    # check for correct characters [0-9a-fA-F] based on lowercase (if necessary)
    correct_chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
    correct = correct and all(c.lower() in correct_chars for c in value[1:])

    if not correct:
        raise common.Invalid(_('Invalid CSS HEX color code {}'.format(value)))

    return value


def validate_styling_dict(key, converted_data, errors, context):
    value = converted_data.get(key)
    for subkey in {'text', 'color'} & set(value.keys()):
        try:
            subvalue = value.get(subkey)
            is_css_hex_color(subvalue)
        except common.Invalid as exception:
            errors[key].append(str(exception))
