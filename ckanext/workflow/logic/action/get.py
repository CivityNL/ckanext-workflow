'''API functions for getting data from CKAN.'''
from ckanext.workflow.model import WorkflowRequest, WorkflowState
from ckan.plugins import toolkit
import ckanext.workflow.logic.schema as workflow_schema

side_effect_free = toolkit.side_effect_free
# logging
import logging

log = logging.getLogger(__name__)


@side_effect_free
def workflow_request_show(context, data_dict):
    ### based on an ID, return the request
    request_id = toolkit.get_or_bust(data_dict, 'id')
    request = WorkflowRequest.get(request_id)
    if not request:
        raise toolkit.ObjectNotFound
    toolkit.check_access('workflow_request_show', context, data_dict)
    return request.as_dict()


@side_effect_free
def workflow_request_list(context, data_dict):
    ### based on query parameters, return the requests
    toolkit.check_access('workflow_request_list', context, data_dict)
    return [request.as_dict() for request in WorkflowRequest.all()]


@side_effect_free
def workflow_state_show(context, data_dict):
    ### based on an ID, return the request
    data_dict, errors = toolkit.navl_validate(data_dict, workflow_schema.workflow_state_show_schema(), context)
    if errors:
        raise toolkit.ValidationError(errors)
    print(data_dict)
    request = WorkflowState.get(package_id=data_dict.get("package_id"))
    if not request:
        raise toolkit.ObjectNotFound
    toolkit.check_access('workflow_state_show', context, data_dict)
    return request.as_dict()


@side_effect_free
def workflow_state_list(context, data_dict):
    ### based on query parameters, return the requests
    toolkit.check_access('workflow_state_list', context, data_dict)
    return [request.as_dict() for request in WorkflowState.all()]
