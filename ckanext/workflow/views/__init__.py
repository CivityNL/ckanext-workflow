from ckanext.workflow.views.package import workflow_dataset
from ckanext.workflow.views.organization import workflow_organization
# logging
import logging
log = logging.getLogger(__name__)

def get_blueprints():
    return [workflow_dataset, workflow_organization]
