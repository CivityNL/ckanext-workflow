from ckan.lib.search import index_for
from ckanext.workflow.plugins.interfaces import IWorkflowRequestController
from ckan.plugins import toolkit, PluginImplementations
import ckanext.workflow.helpers as helpers
from ckanext.workflow.model import WorkflowState, WorkflowRequest
import ckanext.workflow.constants as workflow_constants
import ckanext.workflow.logic.schema as workflow_schema
from ckanext.workflow.plugins.interfaces import IWorkflowPackageStateController
from flask import make_response
# logging
import logging

log = logging.getLogger(__name__)


def workflow_request_update(context, data_dict):
    """

    :param context:
    :param data_dict:
    """
    log.warning("workflow_state_update data_dict = [{}]".format(data_dict))
    model = context["model"]
    session = context["session"]
    user = context["user"]
    actor = model.User.by_name(user)

    print(workflow_schema.workflow_request_update_schema())
    # check if all the information given is valid
    data_dict, errors = toolkit.navl_validate(data_dict, workflow_schema.workflow_request_update_schema(), context)
    if errors:
        raise toolkit.ValidationError(errors)
    log.warning("workflow_state_update data_dict = [{}]".format(data_dict))

    request_id = data_dict.get("id")
    workflow_request = WorkflowRequest.get(request_id)
    context["workflow_request"] = workflow_request

    toolkit.check_access('workflow_request_update', context, data_dict)

    for key in data_dict:
        setattr(workflow_request, key, data_dict[key])

    session.add(workflow_request)

    for plugin in PluginImplementations(IWorkflowRequestController):
        plugin.after_request_update(context, data_dict)

    # Create activity
    activity = model.Activity(
        actor.id, request_id, "updated request", {'request': workflow_request.as_dict(), 'actor': actor.name if actor else None}
    )
    session.add(activity)

    if not context.get('defer_commit'):
        model.repo.commit()

    return workflow_request.as_dict()


STATE_APPROVED = 'approved'
STATE_REJECTED = 'rejected'
STATE_DELETED = 'deleted'
STATE_RESOLVED = 'resolved'




def workflow_state_update(context, data_dict):
    """

    :param context:
    :param data_dict:
    :return:
    """

    session = context["session"]
    model = context["model"]
    user = context["user"]

    actor = model.User.by_name(user)

    # check if all the information given is valid
    data_dict, errors = toolkit.navl_validate(data_dict, workflow_schema.workflow_state_update_schema(), context)
    if errors:
        raise toolkit.ValidationError(errors)

    log.warning("workflow_state_update data_dict = [{}]".format(data_dict))
    package_id, state_id = toolkit.get_or_bust(data_dict, ['package_id', 'state_id'])
    # get the existing WorkflowState (if exists)
    workflow_state = WorkflowState.get(package_id)

    context["workflow_state"] = workflow_state

    # check if the user is allowed to do this action
    toolkit.check_access('workflow_state_update', context, data_dict)

    prev_state = None
    if workflow_state is not None:
        prev_state = workflow_state.state_id

    # stop handling this on a non-update
    if prev_state == state_id:
        return workflow_state.as_dict() if workflow_state is not None else None

    # create or update the WorkflowState (if exists)
    if workflow_state is None:
        workflow_state = WorkflowState(package_id, state_id)
    elif workflow_state.has_requests:
        for request in workflow_state.requests:
            session.delete(request)
            activity_type = "deleted request"
            if request.request_state == state_id:
                activity_type = "resolved request"
            request_activity = model.Activity(
                actor.id, package_id, activity_type, {'request': request.as_dict(), 'actor': actor.name if actor else None}
            )
            session.add(request_activity)

    workflow_state.state_id = state_id
    session.add(workflow_state)

    for plugin in PluginImplementations(IWorkflowPackageStateController):
        plugin.after_state_update(context, data_dict)

    # Create activity
    pkg_dict = toolkit.get_action('package_show')(context, {'id': package_id})

    activity = model.Activity(
        actor.id, package_id, "changed package", {'package': pkg_dict, 'actor': actor.name if actor else None}
    )
    session.add(activity)

    if not context.get('defer_commit'):
        model.repo.commit()

    # update the SOLR index
    index = index_for(model.Package)
    pkg_dict = toolkit.get_action('package_show')(context, {'id': package_id})
    index.update_dict(pkg_dict)

    # return the SOLR index
    return workflow_state.as_dict()
