from ckan.model import package_table, user_table

from ckanext.workflow.common import getLogger
from ckanext.workflow.model.workflow_state import WorkflowState, define_workflow_state_table
from ckanext.workflow.model.workflow_request import WorkflowRequest, define_workflow_request_table
from ckanext.workflow.model.workflow_message import WorkflowMessage, define_workflow_message_table

log = getLogger(__name__)

workflow_state_table = None
workflow_request_table = None
workflow_message_table = None


def setup():
    global workflow_state_table
    global workflow_request_table
    global workflow_message_table

    # STATE

    if workflow_state_table is None:
        workflow_state_table = define_workflow_state_table()
        log.debug('Workflow state table defined in memory')

    # workflow_state_table depends on package_table
    if not package_table.exists():
        log.debug('Workflow state table creation deferred')
    else:
        if not workflow_state_table.exists():
            workflow_state_table.create()
            log.debug('Workflow state table created')
        log.debug('Workflow state table already exists')

    # MESSAGE

    if workflow_message_table is None:
        workflow_message_table = define_workflow_message_table()
        log.debug('Workflow message table defined in memory')

    # workflow_message_table depends on workflow_request_table
    if not all([user_table.exists()]):
        log.debug('Workflow message table creation deferred')
    else:        
        if not workflow_message_table.exists():
            workflow_message_table.create()
            log.debug('Workflow message table created')
        log.debug('Workflow message table already exists')

    # REQUEST

    if workflow_request_table is None:
        workflow_request_table = define_workflow_request_table()
        log.debug('Workflow request table defined in memory')

    # workflow_request_table depends on workflow_state_table
    if not all([workflow_message_table.exists(), workflow_state_table.exists(), user_table.exists()]):
        log.debug('Workflow request table creation deferred')
    else:
        if not workflow_request_table.exists():
            workflow_request_table.create()
            log.debug('Workflow request table created')
        log.debug('Workflow request table already exists')
