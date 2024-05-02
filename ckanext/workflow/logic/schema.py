from ckan.plugins import toolkit
import ckanext.workflow.logic.validators as workflow_validators

empty_if_not_sysadmin = toolkit.get_validator("empty_if_not_sysadmin")
ignore_missing = toolkit.get_validator("ignore_missing")
unicode_safe = toolkit.get_validator("unicode_safe")
not_empty = toolkit.get_validator("not_empty")
boolean_validator = toolkit.get_validator("boolean_validator")
isodate = toolkit.get_validator("isodate")

convert_package_name_or_id_to_id = toolkit.get_converter("convert_package_name_or_id_to_id")
convert_group_name_or_id_to_id = toolkit.get_converter("convert_group_name_or_id_to_id")
convert_user_name_or_id_to_id = toolkit.get_converter("convert_user_name_or_id_to_id")

workflow_request_id_does_not_exist = workflow_validators.request_id_does_not_exist
workflow_organization_id_exists = workflow_validators.organization_id_exists
workflow_state_exists = workflow_validators.state_exists
workflow_request_approval_validator = workflow_validators.request_approval_validator



def workflow_request_list_schema():
    pass


def workflow_request_create_schema():
    return {
        'id': [empty_if_not_sysadmin, ignore_missing, unicode_safe, workflow_request_id_does_not_exist],
        'package_id': [not_empty, unicode_safe, convert_package_name_or_id_to_id],
        'organization_id': [not_empty, unicode_safe, convert_group_name_or_id_to_id, workflow_organization_id_exists],
        'state_id': [not_empty, unicode_safe, workflow_state_exists],

        'request_user_id': [not_empty, unicode_safe, convert_user_name_or_id_to_id],
        'request_state': [not_empty, unicode_safe, workflow_state_exists],
        'request_message': [ignore_missing, unicode_safe],
        'request_timestamp': [empty_if_not_sysadmin, ignore_missing, isodate],

        'process_user_id': [ignore_missing, unicode_safe, convert_user_name_or_id_to_id],
        'process_message': [ignore_missing, unicode_safe],
        'process_timestamp': [empty_if_not_sysadmin, ignore_missing, isodate],
        'process_state': [ignore_missing, unicode_safe, boolean_validator],
        '__after': [workflow_request_approval_validator]
    }


def workflow_request_update_schema():
    return workflow_request_create_schema()
