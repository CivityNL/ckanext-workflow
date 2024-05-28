'''API functions for deleting data from CKAN.'''

from ckanext.workflow.interface import IWorkflowPackageRequestController
from ckan.plugins import PluginImplementations
# logging
import logging
log = logging.getLogger(__name__)


def workflow_request_delete(context, data_dict):
    log.warning("AUTH workflow_request_delete still needs to be implemented")
    return {'success': True}
