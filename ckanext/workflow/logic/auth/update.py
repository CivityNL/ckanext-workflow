from ckanext.workflow.interface import IWorkflowPackageRequestController
from ckan.plugins import toolkit, PluginImplementations
import ckanext.workflow.helpers as helpers
import ckanext.workflow.constants as workflow_constants
from ckanext.workflow.interface import IWorkflowPackageStateController
# logging
import logging
log = logging.getLogger(__name__)


def workflow_request_update(context, data_dict):
    log.warning("AUTH workflow_request_update still needs to be implemented")
    return {'success': True}


def workflow_state_update(context, data_dict):
    log.warning("AUTH workflow_state_update still needs to be implemented")
    return {'success': True}
