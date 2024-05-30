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

list_one_of = workflow_validators.list_one_of
workflow_is_text_function = workflow_validators.is_text_function
workflow_is_function_with_parameters = workflow_validators.is_function_with_parameters

_fn_has_context_and_data_dict = workflow_is_function_with_parameters(["context", "data_dict"])


def workflow_schema(update_actions, roles, states):
    return {
        'states': workflow_state_schema(update_actions, roles, states),
        'transitions': workflow_transition_schema(roles, states),
        '__extras': [ignore],
    }


def workflow_state_schema(update_actions, permissions, states):
    return {
        'id': [not_empty, unicode_safe],
        'label': [not_empty, workflow_is_text_function],
        'dataset_fields': [],
        'update_actions': workflow_state_update_action_schema(update_actions, permissions, states),
        '__extras': [ignore],
    }


def workflow_state_update_action_schema(update_actions, permissions, states):
    return {
        'action': [not_empty, one_of(update_actions)],
        'permission': [one_of(permissions)],
        'to_state': [one_of(states)],
        '__extras': [ignore],
    }


def workflow_update_action_schema():
    return {
        'action': [not_empty, unicode_safe],
        'getter': [ignore_empty, _fn_has_context_and_data_dict],
        '__extras': [ignore],
    }


def workflow_transition_schema(roles, states):
    return {
        'label': [not_empty, workflow_is_text_function],
        'from_state': [not_empty, unicode_safe, one_of(states)],
        'to_state': [not_empty, unicode_safe, one_of(states)],
        'can_request': [ignore_empty, list_one_of(roles)],
        'can_approve': [ignore_empty, list_one_of(roles)],
        'can_assign': [ignore_empty, list_one_of(roles)],
        'request_message_required': [ignore_empty, boolean_validator],
        'approve_message_required': [ignore_empty, boolean_validator],
        'reject_message_required': [ignore_empty, boolean_validator],
        '__extras': [ignore],
    }


def workflow_styling_schema():
    return {
        'text': '#123456',
        'background': '#123456'
    }
