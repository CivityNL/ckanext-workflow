'''API functions for getting data from CKAN.'''
from ckanext.workflow.model import WorkflowPackageRequest, WorkflowPackageState
from ckan.plugins import toolkit
import ckanext.workflow.logic.schema as workflow_schema
from ckanext.authorization.common import side_effect_free, getLogger, ObjectNotFound, get_or_bust, navl_validate, ValidationError
from ckanext.authorization.common.toolkit import check_access


log = getLogger(__name__)


@side_effect_free
def workflow_request_show(context, data_dict):
    ### based on an ID, return the request
    request_id = get_or_bust(data_dict, 'id')
    request = WorkflowPackageRequest.get(request_id)
    if not request:
        raise ObjectNotFound
    check_access('workflow_request_show', context, data_dict)
    return request.as_dict()


@side_effect_free
def workflow_request_list(context, data_dict):
    ### based on query parameters, return the requests
    check_access('workflow_request_list', context, data_dict)
    return [request.as_dict() for request in WorkflowPackageRequest.all()]


@side_effect_free
def workflow_state_show(context, data_dict):
    ### based on an ID, return the request
    data_dict, errors = navl_validate(data_dict, workflow_schema.workflow_state_show_schema(), context)
    if errors:
        raise ValidationError(errors)
    print(data_dict)
    request = WorkflowPackageState.get(package_id=data_dict.get("package_id"))
    if not request:
        raise ObjectNotFound
    check_access('workflow_state_show', context, data_dict)
    return request.as_dict()


@side_effect_free
def workflow_state_list(context, data_dict):
    ### based on query parameters, return the requests
    check_access('workflow_state_list', context, data_dict)
    return [request.as_dict() for request in WorkflowPackageState.all()]
