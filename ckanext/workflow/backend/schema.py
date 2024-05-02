from ckan.plugins import toolkit
import ckanext.workflow.backend.validators as workflow_validators


unicode_safe = toolkit.get_validator("unicode_safe")
not_empty = toolkit.get_validator("not_empty")
boolean_validator = toolkit.get_validator("boolean_validator")
one_of = toolkit.get_validator("one_of")
ignore_empty = toolkit.get_validator("ignore_empty")

workflow_is_text_function = workflow_validators.is_text_function
workflow_list_one_of_validators = workflow_validators.list_one_of_validators
workflow_is_function_with_parameters = workflow_validators.is_function_with_parameters

_fn_has_context_and_data_dict = workflow_is_function_with_parameters(["context", "data_dict"])


def _can_update(roles):
    return workflow_list_one_of_validators(
        [one_of(roles), workflow_is_function_with_parameters(["context", "pkg_dict"])])


def _on_update(states):
    return workflow_list_one_of_validators([one_of(states), _fn_has_context_and_data_dict])


def workflow_state_schema(roles, states):
    return {
        'id': [not_empty, unicode_safe],
        'label': [not_empty, workflow_is_text_function],
        'dataset_fields': [],
        'can_update': [ignore_empty, _can_update(roles)],
        'on_update': [ignore_empty, _on_update(states)],
        'update_actions': workflow_state_update_action_schema(),
        'can_be_skipped': [boolean_validator]
    }


def workflow_state_update_action_schema():
    return {
        'action': [not_empty, unicode_safe],
        'getter': [ignore_empty, _fn_has_context_and_data_dict]
    }


def workflow_update_action_schema():
    return {
        'action': [not_empty, unicode_safe],
        'getter': [ignore_empty, _fn_has_context_and_data_dict]
    }


def workflow_transition_schema(roles, states):
    return {
        'label': [not_empty, workflow_is_text_function],
        'from_state': [not_empty, unicode_safe, one_of(states)],
        'to_state': [not_empty, unicode_safe, one_of(states)],
        'can_request': [ignore_empty, _can_update(roles)],
        'can_approve': [ignore_empty, _can_update(roles)],
        'request_required': [ignore_empty, boolean_validator],
        'request_message_required': [ignore_empty, boolean_validator],
        'approve_message_required': [ignore_empty, boolean_validator],
        'reject_message_required': [ignore_empty, boolean_validator]
    }
