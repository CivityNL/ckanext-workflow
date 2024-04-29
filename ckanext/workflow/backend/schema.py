from ckan.plugins import toolkit
import ckanext.workflow.backend.validators as workflow_validators

empty_if_not_sysadmin = toolkit.get_validator("empty_if_not_sysadmin")
ignore_missing = toolkit.get_validator("ignore_missing")
unicode_safe = toolkit.get_validator("unicode_safe")
package_id_exists = toolkit.get_validator("package_id_exists")
not_empty = toolkit.get_validator("not_empty")
user_id_exists = toolkit.get_validator("user_id_exists")
boolean_validator = toolkit.get_validator("boolean_validator")
isodate = toolkit.get_validator("isodate")
one_of = toolkit.get_validator("one_of")
ignore_empty = toolkit.get_validator("ignore_empty")

convert_package_name_or_id_to_id = toolkit.get_converter("convert_package_name_or_id_to_id")
convert_group_name_or_id_to_id = toolkit.get_converter("convert_group_name_or_id_to_id")
convert_user_name_or_id_to_id = toolkit.get_converter("convert_user_name_or_id_to_id")

workflow_request_id_does_not_exist = workflow_validators.request_id_does_not_exist
workflow_organization_id_exists = workflow_validators.organization_id_exists
workflow_state_exists = workflow_validators.state_exists
workflow_request_approval_validator = workflow_validators.request_approval_validator
workflow_is_text_function = workflow_validators.is_text_function
workflow_list_one_of = workflow_validators.list_one_of
workflow_one_of_validators = workflow_validators.one_of_validators
workflow_list_one_of_validators = workflow_validators.list_one_of_validators
workflow_is_function_with_parameters = workflow_validators.is_function_with_parameters


def workflow_state_schema(roles, states):
    from_data_dict = workflow_is_function_with_parameters(["context", "data_dict"])
    can_update = workflow_list_one_of_validators([one_of(roles), workflow_is_function_with_parameters(["context", "pkg_dict"])])
    on_update = workflow_list_one_of_validators([one_of(states), from_data_dict])
    return {
        'id': [not_empty, unicode_safe],
        'label': [not_empty, workflow_is_text_function],
        'dataset_fields': [],
        'can_update': [ignore_empty, can_update],
        'on_update': [ignore_empty, on_update],
        'update_actions': workflow_state_update_action_schema(),
        'can_be_skipped': [boolean_validator]
    }


def workflow_state_update_action_schema():
    from_data_dict = workflow_is_function_with_parameters(["context", "data_dict"])
    return {
        'action': [not_empty, unicode_safe],
        'getter': [ignore_empty, from_data_dict]
    }


def workflow_update_action_schema():
    from_data_dict = workflow_is_function_with_parameters(["context", "data_dict"])
    return {
        'action': [not_empty, unicode_safe],
        'getter': [ignore_empty, from_data_dict]
    }


def workflow_transition_schema(roles, states):
    can = workflow_list_one_of_validators([one_of(roles), workflow_is_function_with_parameters(["context", "pkg_dict"])])
    return {
        'label': [not_empty, workflow_is_text_function],
        'from_state': [not_empty, unicode_safe, one_of(states)],
        'to_state': [not_empty, unicode_safe, one_of(states)],
	    'can_request': [ignore_empty, can],
        'can_approve': [ignore_empty, can],
        'request_required': [ignore_empty, boolean_validator],
        'request_message_required': [ignore_empty, boolean_validator],
        'approve_message_required': [ignore_empty, boolean_validator],
        'reject_message_required': [ignore_empty, boolean_validator]
    }
