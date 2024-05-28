'''API functions for getting data from CKAN.'''
from ckanext.workflow.model import WorkflowPackageRequest
from ckan.plugins import toolkit

side_effect_free = toolkit.side_effect_free
# logging
import logging

log = logging.getLogger(__name__)


@side_effect_free
def workflow_request_show(context, data_dict):
    log.warning("AUTH workflow_request_show still needs to be implemented")
    return {'success': True}


@side_effect_free
def workflow_request_list(context, data_dict):
    log.warning("AUTH workflow_request_list still needs to be implemented")
    return {'success': True}

@side_effect_free
def workflow_state_show(context, data_dict):
    log.warning("AUTH workflow_state_show still needs to be implemented")
    return {'success': True}


@side_effect_free
def workflow_state_list(context, data_dict):
    log.warning("AUTH workflow_state_list still needs to be implemented")
    return {'success': True}
