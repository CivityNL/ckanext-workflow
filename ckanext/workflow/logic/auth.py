'''API functions for creating data from CKAN.'''

from ckanext.workflow.interface import IWorkflowRequestController
from ckan.plugins import toolkit, PluginImplementations
from ckanext.workflow.model import WorkflowRequest, WorkflowState
import ckanext.workflow.logic.schema as workflow_schema
import ckanext.workflow.common as common
log = common.getLogger(__name__)
from ckanext.workflow.interface import IWorkflowRequestController
from ckan.plugins import toolkit, PluginImplementations
import ckanext.workflow.helpers as helpers
from ckanext.workflow.interface import IWorkflowStateController
# logging
import logging
log = logging.getLogger(__name__)
from ckanext.workflow.interface import IWorkflowRequestController
from ckan.plugins import PluginImplementations
# logging
import logging
log = logging.getLogger(__name__)
'''API functions for getting data from CKAN.'''
from ckanext.workflow.model import WorkflowRequest
from ckan.plugins import toolkit

side_effect_free = toolkit.side_effect_free
# logging
import logging

'''API functions for deleting data from CKAN.'''

log = logging.getLogger(__name__)
def workflow_dataset_request_create(context, data_dict):

    data_dict, errors = common.navl_validate(data_dict, workflow_schema.workflow_dataset_request_create_schema(), context)

    user = context['auth_user_obj']
    request_fields = ['package_id', 'request_user_id', 'request_state']

    if any(field in errors for field in request_fields):
        raise common.ValidationError(errors)

    package_id, request_user_id, request_state = common.get_or_bust(data_dict, request_fields)
    workflow_state = helpers._get_state_id(package_id)

    log.warning("AUTH workflow_dataset_request_create still needs to be implemented")

    return {'success': True}




def workflow_dataset_request_delete(context, data_dict):
    log.warning("AUTH workflow_dataset_request_delete still needs to be implemented")
    return {'success': True}



@side_effect_free
def workflow_dataset_request_show(context, data_dict):
    log.warning("AUTH workflow_dataset_request_show still needs to be implemented")
    return {'success': True}


@side_effect_free
def workflow_dataset_request_list(context, data_dict):
    log.warning("AUTH workflow_dataset_request_list still needs to be implemented")
    return {'success': True}


def workflow_dataset_request_update(context, data_dict):
    log.warning("AUTH workflow_dataset_request_update still needs to be implemented")
    return {'success': True}


def workflow_dataset_state_update(context, data_dict):
    log.warning("AUTH workflow_dataset_state_update still needs to be implemented")
    return {'success': True}

def workflow_request_activity_list(context, data_dict):
    log.warning("AUTH workflow_request_activity_list still needs to be implemented")
    return {'success': True}


def workflow_dataset_request_message_create(context, data_dict):
    log.warning("AUTH workflow_dataset_request_message_create still needs to be implemented")
    return {'success': True}
