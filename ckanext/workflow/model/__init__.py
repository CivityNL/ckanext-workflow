# logging
import logging
from ckanext.workflow.model.workflow_request import WorkflowRequest, define_workflow_request_table
from ckanext.workflow.model.workflow_state import WorkflowState, define_workflow_state_table
from ckanext.workflow.model.workflow_group import WorkflowGroup, define_workflow_group_table

import ckan.model as model

log = logging.getLogger(__name__)


workflow_request_table = None
workflow_state_table = None
workflow_group_table = None


def setup():
    global workflow_request_table
    global workflow_state_table
    global workflow_group_table

    if workflow_state_table is None:
        workflow_state_table = define_workflow_state_table()
        log.debug('Workflow state table defined in memory')
    if workflow_request_table is None:
        workflow_request_table = define_workflow_request_table()
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
    #
    # log.warning(WorkflowState.all())
    # log.warning(WorkflowRequest.all())
    #
    # orgs = model.Session.query(model.Group.id).filter(model.Group.is_organization).all()
    # for org in orgs:
    #     for state in WorkflowState.get_for_organization(org):
    #         log.warning("{} :: {} with {}".format(
    #             org, state, state._requests
    #         ))
