from ckan.lib.search import index_for
from ckanext.authorization.backend import AuthorizationBackend
from ckanext.workflow.backend import WorkflowBackend
from ckanext.workflow.interface import IWorkflowPackageRequestController
from ckan.plugins import toolkit, PluginImplementations
from ckanext.workflow.model import WorkflowPackageState, WorkflowPackageRequest
import ckanext.workflow.logic.schema as workflow_schema
from ckanext.workflow.interface import IWorkflowPackageStateController
from ckanext.workflow.common import get_action, chained_action
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
    workflow_request = WorkflowPackageRequest.get(request_id)

    toolkit.check_access('workflow_request_update', context, data_dict)

    for key in data_dict:
        setattr(workflow_request, key, data_dict[key])

    session.add(workflow_request)

    for plugin in PluginImplementations(IWorkflowPackageRequestController):
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


def print_session(session, prefix=None):
    for attr in ['new', 'dirty', 'deleted']:
        for entity in getattr(session, attr):
            pass
            # log.info(f"{prefix} Session.{attr} = {entity}")




def workflow_state_update(context, data_dict):
    """

    :param context:
    :param data_dict:
    :return:
    """
    session = context["session"]
    model = context["model"]
    user = context["user"]

    log.info(f"defer_commit={context.get('defer_commit', None)}")
    log.info(f"ignore_auth={context.get('ignore_auth', None)}")
    log.info(f"ignore_workflow={context.get('ignore_workflow', None)}")

    actor = model.User.by_name(user)

    x = AuthorizationBackend.get_datasets_with_user_permission(
        actor.id,
        'read'
    )
    print(x)

    print_session(session, 'fresh')
    # check if all the information given is valid
    data_dict, errors = toolkit.navl_validate(data_dict, workflow_schema.workflow_state_update_schema(), context)
    if errors:
        raise toolkit.ValidationError(errors)

    log.warning("workflow_state_update data_dict = [{}]".format(data_dict))
    package_id, state_id = toolkit.get_or_bust(data_dict, ['package_id', 'state_id'])

    # get the existing WorkflowPackageState (if exists)
    workflow_state = WorkflowPackageState.get(package_id)

    # check if the user is allowed to do this action
    toolkit.check_access('workflow_state_update', context, data_dict)

    prev_state = None
    if workflow_state is not None:
        prev_state = workflow_state.state_id

    # stop handling this on a non-update
    if prev_state == state_id:
        return workflow_state.as_dict() if workflow_state is not None else None

    # create or update the WorkflowPackageState (if exists)
    if workflow_state is None:
        workflow_state = WorkflowPackageState(package_id, state_id)
    elif workflow_state.has_requests:
        for request in workflow_state.requests:
            activity_type = "deleted request"
            request.set_deleted(actor.id)
            if request.request_state == state_id:
                request.set_resolved(actor.id)
            session.add(request)
            request_activity = model.Activity(
                actor.id, package_id, activity_type, {'request': request.as_dict(), 'actor': actor.name if actor else None}
            )
            session.add(request_activity)
    else:
        workflow_state.state_id = state_id

    session.add(workflow_state)

    print_session(session, 'after adding')
    session.flush()

    if WorkflowBackend.get_state(state_id).dataset_fields:
        # make sure this patch will be ignored
        package_patch_context = dict(context, defer_commit=True, ignore_auth=True, ignore_workflow=True)
        package_patch_data_dict = dict(WorkflowBackend.get_state(state_id).dataset_fields, id=package_id)
        get_action('package_patch')(package_patch_context, package_patch_data_dict)

    session.flush()

    print_session(session, 'after adding')

    for plugin in PluginImplementations(IWorkflowPackageStateController):
        plugin.after_state_update(context, data_dict)

    # Create activity
    pkg_dict = toolkit.get_action('package_show')(context, {'id': package_id})

    activity = model.Activity(
        actor.id, package_id, "changed package", {'package': pkg_dict, 'actor': actor.name if actor else None}
    )
    session.add(activity)

    print_session(session, 'before commit')
    if not context.get('defer_commit'):
        model.repo.commit()

    # update the SOLR index
    index = index_for(model.Package)
    pkg_dict = toolkit.get_action('package_show')(context, {'id': package_id})
    index.update_dict(pkg_dict)

    # return the SOLR index
    return pkg_dict


@chained_action
def package_update(original_action, context, data_dict):
    print("before package_update")
    result =  original_action(context, data_dict)
    print("after package_update")
    return result