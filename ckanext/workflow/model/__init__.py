import logging
from ckanext.workflow.model.workflow_request import WorkflowPackageRequest, define_workflow_package_request_table
from ckanext.workflow.model.workflow_state import WorkflowPackageState, define_workflow_package_state_table
from ckanext.workflow.model.workflow_group import WorkflowGroup, define_workflow_group_table

log = logging.getLogger(__name__)

workflow_request_table = None
workflow_state_table = None
workflow_group_table = None


def setup():
    global workflow_request_table
    global workflow_state_table
    global workflow_group_table

    if workflow_state_table is None:
        workflow_state_table = define_workflow_package_state_table()
        log.debug('Workflow state table defined in memory')
    if workflow_request_table is None:
        workflow_request_table = define_workflow_package_request_table()
        log.debug('Workflow request table defined in memory')
    if workflow_group_table is None:
        workflow_group_table = define_workflow_group_table()
        log.debug('Workflow group table defined in memory')
    if not workflow_state_table.exists():
        workflow_state_table.create()
        log.debug('Workflow state table created')
    if not workflow_request_table.exists():
        workflow_request_table.create()
        log.debug('Workflow request table created')
    if not workflow_group_table.exists():
        workflow_group_table.create()
        log.debug('Workflow group table created')
