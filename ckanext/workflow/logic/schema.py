"""
Schema's for validation of the `data_dict` argument for actions
"""

import ckanext.workflow.logic.validators as workflow_validators
from ckanext.workflow.model.workflow_package_request import REQUEST_STATES
import ckanext.workflow.common as common
from ckanext.workflow.utils import sphinx_decorator

log = common.getLogger(__name__)

workflow_request_id_does_not_exist = workflow_validators.request_id_does_not_exist
workflow_request_id_exists = workflow_validators.request_id_exists
workflow_state_exists = workflow_validators.state_exists
default_current_user = workflow_validators.default_current_user
request_does = workflow_validators.request_does
package_has_workflow_state = workflow_validators.package_has_workflow_state
request_message_required = workflow_validators.request_message_required
transition_exists = workflow_validators.transition_exists
process_user_id_required = workflow_validators.process_user_id_required
process_message_required = workflow_validators.process_message_required


def ignore_extras(schema_func):
    """
    This function can be used as a decorator for any other functions returning
    schema's for which any additional fields (a.k.a. 'extras') should be ignored.

    :param schema_func: Schema generating function
    """

    def _ignore_extras():
        """
        gsdfgdsfgsdfg
        :return:
        """
        schema = schema_func()
        extras = schema.get('__extras', [])
        if common.ignore not in extras:
            extras.append(common.ignore)
            schema['__extras'] = extras
        return schema

    sphinx_decorator(ignore_extras, _ignore_extras, schema_func)
    return _ignore_extras


@ignore_extras
def workflow_dataset_request_list_schema():
    log.warning("SCHEMA workflow_dataset_request_list_schema still needs to be implemented")
    return {}


@ignore_extras
def workflow_dataset_request_create_schema() -> dict:
    """
    This schema is used when trying to create a :class:`ckanext.workflow.model.WorkflowPackageRequest` object.

    :return: object
    :rtype: dict
    """
    return {
        'package_id': [
            common.not_empty, common.unicode_safe, common.convert_package_name_or_id_to_id, package_has_workflow_state
        ],
        'request_user_id': [common.not_empty, common.unicode_safe, common.convert_user_name_or_id_to_id],
        'request_state': [common.not_empty, common.unicode_safe, workflow_state_exists],
        'request_message': [common.ignore_empty, common.unicode_safe],
        '__after': [request_does, transition_exists(), request_message_required()],
    }


@ignore_extras
def workflow_dataset_request_update_schema():
    schema = workflow_dataset_request_create_schema()
    schema['id'] = [common.not_empty, common.unicode_safe, workflow_request_id_exists]

    schema['process_user_id'] = [common.ignore_empty, common.unicode_safe, common.convert_user_name_or_id_to_id]
    schema['process_message'] = [common.ignore_empty, common.unicode_safe]
    schema['process_state'] = [common.not_empty, common.unicode_safe, common.one_of(REQUEST_STATES)]
    schema['__after'].remove(request_does)
    schema['__after'].extend(
        [transition_exists(), request_message_required(), process_user_id_required(), process_message_required()]
    )
    return schema


@ignore_extras
def workflow_dataset_request_show_schema():
    return {
        'id': [common.not_empty, common.unicode_safe, workflow_request_id_exists],
    }

@ignore_extras
def workflow_dataset_request_delete_schema():
    return workflow_dataset_request_show_schema()


@ignore_extras
def workflow_dataset_state_update_schema():
    """
    """
    return {
        'package_id': [common.not_empty, common.unicode_safe, common.convert_package_name_or_id_to_id],
        'state_id': [common.not_empty, common.unicode_safe, workflow_state_exists]
    }
