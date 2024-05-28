'''API functions for deleting data from CKAN.'''
from ckanext.workflow.model import WorkflowPackageRequest
from ckanext.workflow.interface import IWorkflowPackageRequestController
from ckan.plugins import PluginImplementations, toolkit
import ckanext.workflow.logic.schema as workflow_schema
# logging
import logging
log = logging.getLogger(__name__)


def workflow_request_delete(context, data_dict):
    """

    :param context:
    :param data_dict:
    """
    log.warning("workflow_request_delete")
    session = context["session"]
    model = context["model"]
    user = context["user"]

    actor = model.User.by_name(user)

    # check if all the information given is valid
    data_dict, errors = toolkit.navl_validate(data_dict, workflow_schema.workflow_request_delete_schema(), context)
    if errors:
        raise toolkit.ValidationError(errors)

    # check if the user is allowed to do this action
    toolkit.check_access('workflow_request_delete', context, data_dict)

    request_id = toolkit.get_or_bust(data_dict, 'id')
    # get the existing WorkflowPackageState (if exists)
    workflow_request = WorkflowPackageRequest.get(request_id)

    session.delete(workflow_request)

    for plugin in PluginImplementations(IWorkflowPackageRequestController):
        plugin.after_request_delete(context, data_dict)

    request_activity = model.Activity(
        actor.id, request_id, "deleted request", {'request': workflow_request.as_dict(), 'actor': actor.name if actor else None}
    )
    session.add(request_activity)

    if not context.get('defer_commit'):
        model.repo.commit()
