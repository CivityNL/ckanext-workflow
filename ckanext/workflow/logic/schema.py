"""
Schema's for validation of the `data_dict` argument for actions
"""

import ckanext.workflow.logic.validators as workflow_validators
from ckanext.workflow.model.workflow_message import WorkflowMessage
from ckanext.workflow.model.workflow_request import REQUEST_STATES
from ckanext.workflow.model import WorkflowState
import ckanext.workflow.common as common
from ckan.logic.schema import default_pagination_schema as _default_pagination_schema

log = common.getLogger(__name__)

default = common.toolkit.get_validator("default")
json_list_or_string = common.toolkit.get_validator("json_list_or_string")

workflow_request_id_does_not_exist = workflow_validators.request_id_does_not_exist
workflow_request_id_exists = workflow_validators.request_id_exists
workflow_state_exists = workflow_validators.state_exists
default_current_user = workflow_validators.default_current_user
request_does = workflow_validators.request_does
request_message_required = workflow_validators.request_message_required
transition_exists = workflow_validators.transition_exists
process_user_id_required = workflow_validators.process_user_id_required
process_message_required = workflow_validators.process_message_required
list_one_of = workflow_validators.list_one_of
list_validator = workflow_validators.list_validator
workflow_message_exists = workflow_validators.message_exists

workflow_state_does_not_exist_for_package = workflow_validators.workflow_state_does_not_exist_for_package
workflow_state_exists_for_package = workflow_validators.workflow_state_exists_for_package
workflow_message_exists = workflow_validators.workflow_message_exists
workflow_organization_id_exists = workflow_validators.organization_id_exists
workflow_reference_object_exists = workflow_validators.reference_object_exists

def workflow_state_create_schema():
    return {
        'package_id': [common.not_empty, common.unicode_safe, common.convert_package_name_or_id_to_id, workflow_state_does_not_exist_for_package],
        'state_id': [common.not_empty, common.unicode_safe, workflow_state_exists]
    }

def workflow_state_update_schema():
    return {
        'package_id': [common.not_empty, common.unicode_safe, common.convert_package_name_or_id_to_id, workflow_state_exists_for_package],
        'state_id': [common.not_empty, common.unicode_safe, workflow_state_exists]
    }

def workflow_state_patch_schema():
    return workflow_state_update_schema()

def workflow_state_delete_schema():
    return {
        'package_id': [common.not_empty, common.unicode_safe, common.convert_package_name_or_id_to_id, workflow_state_exists_for_package],
    }

def workflow_state_purge_schema():
    return {
        'package_id': [common.not_empty, common.unicode_safe, common.convert_package_name_or_id_to_id, workflow_state_exists_for_package],
    }

def workflow_state_show_schema():
    return {
        'package_id': [common.not_empty, common.unicode_safe, common.convert_package_name_or_id_to_id, workflow_state_exists_for_package],
    }

def workflow_state_list_schema():
    schema = workflow_default_list_schema(WorkflowState.get_column_names(), WorkflowState)
    schema['owner_org'] = [common.ignore_missing, common.convert_to_list_if_string, list_validator(workflow_organization_id_exists)]
    schema['package_state'] = [common.ignore_missing, common.convert_to_list_if_string, list_one_of(['active', 'deleted', 'pending'])]
    log.warning("SCHEMA workflow_state_list_schema still needs to be implemented")
    return schema

##################
# REQUESTS
##################


def workflow_request_create_schema() -> dict:
    """
    This schema is used when trying to create a :class:`ckanext.workflow.model.WorkflowRequest` object.

    :return: object
    :rtype: dict
    """
    return {
        'package_id': [common.not_empty, common.unicode_safe, common.convert_package_name_or_id_to_id],
        'request_user_id': [common.not_empty, common.unicode_safe, common.convert_user_name_or_id_to_id],
        'request_state': [common.not_empty, common.unicode_safe, workflow_state_exists],
        'request_message': [common.ignore_empty, common.unicode_safe],
        '__after': [request_does, transition_exists(), request_message_required()],
    }

def workflow_request_update_schema():
    schema = workflow_request_create_schema()
    schema['id'] = [common.not_empty, common.unicode_safe, workflow_request_id_exists]

    schema['process_user_id'] = [common.ignore_empty, common.unicode_safe, common.convert_user_name_or_id_to_id]
    schema['process_message'] = [common.ignore_empty, common.unicode_safe]
    schema['process_state'] = [common.not_empty, common.unicode_safe, common.one_of(REQUEST_STATES)]
    schema['__after'].remove(request_does)
    schema['__after'].extend(
        [transition_exists(), request_message_required(), process_user_id_required(), process_message_required()]
    )
    return schema

def workflow_request_patch_schema():
    return workflow_request_update_schema()

def workflow_request_delete_schema():
    return {
        'id': [common.not_empty, common.unicode_safe, workflow_request_id_exists]
    }

def workflow_request_purge_schema():
    return workflow_request_delete_schema()

def workflow_request_show_schema():
    return {
        'id': [common.not_empty, common.unicode_safe, workflow_request_id_exists],
    }

def workflow_request_list_schema():
    log.warning("SCHEMA workflow_state_list_schema still needs to be implemented")
    return {}

############################
# MESSAGES

def workflow_message_create_schema() -> dict:
    """
    This schema is used when trying to create a :class:`ckanext.workflow.model.WorkflowRequest` object.

    :return: object
    :rtype: dict
    """
    return {
        'created': [common.ignore_not_sysadmin, common.ignore_empty, common.unicode_safe, common.isodate],
        'modified': [common.ignore_not_sysadmin, common.ignore_empty, common.unicode_safe, common.isodate],
        'state': [common.ignore_not_sysadmin, default('active'), common.unicode_safe, common.one_of(['active', 'deleted'])],
        'user_id': [common.ignore_not_sysadmin, default_current_user, common.unicode_safe, common.convert_user_name_or_id_to_id],
        'content': [common.not_empty, common.unicode_safe],
        'reference_type': [common.not_empty, common.unicode_safe, common.one_of(['package', 'workflow_request', 'workflow_message'])],
        'reference_id': [common.not_empty, common.unicode_safe],
        '__after': [workflow_reference_object_exists],
    }

def workflow_message_update_schema():
    """
    """
    return {
        'id': [common.not_empty, common.unicode_safe, workflow_message_exists],
        'created': [common.ignore_not_sysadmin, common.ignore_empty, common.unicode_safe, common.isodate],
        'modified': [common.ignore_not_sysadmin, common.ignore_empty, common.unicode_safe, common.isodate],
        'state': [common.ignore_not_sysadmin, common.ignore_empty, common.unicode_safe, common.one_of(['active', 'deleted'])],
        'user_id': [common.ignore_not_sysadmin, common.ignore_empty, common.unicode_safe, common.convert_user_name_or_id_to_id],
        'content': [common.ignore_missing, common.not_empty, common.unicode_safe],
        'reference_type': [common.ignore_not_sysadmin, common.ignore_empty, common.unicode_safe, common.one_of(['package', 'workflow_request', 'workflow_message']), common.both_not_empty('reference_id')],
        'reference_id': [common.ignore_not_sysadmin, common.ignore_empty, common.unicode_safe, common.both_not_empty('reference_type')],
        '__after': [workflow_reference_object_exists],
    }


def workflow_message_patch_schema():
    return workflow_message_update_schema()

def workflow_message_delete_schema():
    return {
        'id': [common.not_empty, common.unicode_safe, workflow_message_exists]
    }

def workflow_message_purge_schema():
    return workflow_message_delete_schema()

def workflow_message_show_schema():
    return {
        'id': [common.not_empty, common.unicode_safe, workflow_message_exists]
    }

def workflow_message_list_schema():
    log.warning("SCHEMA workflow_state_list_schema still needs to be implemented")
    schema = workflow_default_list_schema(['num_replies', 'latest_activity', 'reference_id'], WorkflowMessage)
    schema['num_replies'] = [common.ignore_missing, common.natural_number_validator]
    schema['num_replies_from'] = [common.ignore_missing, common.natural_number_validator]
    schema['num_replies_to'] = [common.ignore_missing, common.natural_number_validator]
    schema['reference_id'] = [common.ignore_missing, common.not_empty, common.unicode_safe]
    return schema



#########################


def workflow_request_activity_list_schema():
    schema = _default_pagination_schema()
    schema['id'] = [common.not_missing, common.unicode_safe, workflow_request_id_exists]
    schema['limit'] = [
        common.configured_default('ckan.activity_list_limit', 31),
        common.natural_number_validator,
        common.limit_to_configured_maximum('ckan.activity_list_limit_max', 100)]
    schema['include_hidden_activity'] = [
        common.ignore_missing, common.ignore_not_sysadmin, common.boolean_validator]
    return schema

def workflow_default_list_schema(sortable_fields, cls):
    print(cls)
    print(cls.filter_fields())
    print(cls.order_fields())
    print(cls.facet_fields())
    list_one_of_validator = list_one_of(list(cls.order_fields().keys()) + [f"{f} {p}" for f in cls.order_fields() for p in ['desc', 'asc']])
    return {
        'limit': [common.ignore_missing, common.natural_number_validator],
        'offset': [common.ignore_missing, common.natural_number_validator],
        'order_by': [default('latest_activity desc'), json_list_or_string, list_one_of_validator],
        'created_from': [common.ignore_missing, common.isodate],
        'created_to': [common.ignore_missing, common.isodate],
        'modified_from': [common.ignore_missing, common.isodate],
        'modified_to': [common.ignore_missing, common.isodate],
        'state': [common.ignore_not_sysadmin, default('active'), json_list_or_string, list_one_of(['active', 'deleted'])],
        'facet': [common.ignore_missing, common.boolean_validator],
        'facet_mincount': [common.ignore_missing, common.natural_number_validator],
        'facet_limit': [common.ignore_missing, common.natural_number_validator],
        'facet_field': [common.ignore_missing, json_list_or_string, list_one_of_validator]
    }
