from ckan.plugins import toolkit
import ckanext.workflow.backend.validators as workflow_validators

# logging
import logging
log = logging.getLogger(__name__)

unicode_safe = toolkit.get_validator("unicode_safe")
not_empty = toolkit.get_validator("not_empty")
boolean_validator = toolkit.get_validator("boolean_validator")
one_of = toolkit.get_validator("one_of")
ignore_empty = toolkit.get_validator("ignore_empty")
ignore = toolkit.get_validator("ignore")
if_empty_same_as = toolkit.get_validator("if_empty_same_as")

list_one_of = workflow_validators.list_one_of
is_action = workflow_validators.is_action
one_of_validators = workflow_validators.one_of_validators
workflow_is_text_function = workflow_validators.is_text_function
workflow_is_function_with_parameters = workflow_validators.is_function_with_parameters
is_css_hex_color = workflow_validators.is_css_hex_color
validate_styling_dict = workflow_validators.validate_styling_dict

_fn_has_context_and_data_dict = workflow_is_function_with_parameters(["context", "data_dict"])

def workflow_schema(update_actions, permissions, states):
    return {
        'states': workflow_state_schema(update_actions, permissions, states),
        'transitions': workflow_transition_schema(permissions, states),
        '__extras': [ignore],
    }


def workflow_state_schema(update_actions, permissions, states):
    return {
        'id': [not_empty, unicode_safe],
        'label': [not_empty, workflow_is_text_function],
        'styling': [ignore_empty, validate_styling_dict],
        'dataset_fields': [],
        'update_actions': workflow_state_update_action_schema(update_actions, permissions, states),
        '__extras': [ignore],
    }


def workflow_state_update_action_schema(update_actions, permissions, states):
    return {
        'action': [not_empty, one_of(update_actions)],
        'permission': [one_of(permissions)],
        'dataset_field': [ignore_empty],
        'to_state': [if_empty_same_as('id'), one_of(states)],
        '__extras': [ignore],
    }


def workflow_update_action_schema():
    return {
        'action': [not_empty, unicode_safe, is_action],
        'getter': [ignore_empty, _fn_has_context_and_data_dict],
        '__extras': [ignore],
    }


def workflow_transition_schema(permissions, states):
    return {
        'label': [not_empty, workflow_is_text_function],
        'styling': [ignore_empty, validate_styling_dict],
        'from_state': [not_empty, unicode_safe, one_of(states)],
        'to_state': [not_empty, unicode_safe, one_of(states)],
        'can_request': [ignore_empty, list_one_of(permissions)],
        'can_approve': [ignore_empty, list_one_of(permissions)],
        'can_assign': [ignore_empty, list_one_of(permissions)],
        'request_message_required': [ignore_empty, boolean_validator],
        'approve_message_required': [ignore_empty, boolean_validator],
        'reject_message_required': [ignore_empty, boolean_validator],
        '__extras': [ignore],
    }


def workflow_styling_schema():
    return {
        'text': [not_empty, is_css_hex_color],
        'background': [not_empty, is_css_hex_color],
    }
