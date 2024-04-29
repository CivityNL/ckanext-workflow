from ckanext.workflow.views.package import workflow_dataset
from ckanext.workflow.views.organization import workflow_organization


def get_blueprints():
    return [workflow_dataset, workflow_organization]
