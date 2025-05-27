"""
    AFGAFASDFASDFASDFSAF


"""

from ckan.lib.search import index_for
from ckanext.workflow.backend import WorkflowBackend
from ckanext.workflow.interface import IWorkflowPackageRequestController
from ckan.plugins import toolkit, PluginImplementations
from ckanext.workflow.logic import workflow_action_schema_decorator
from ckanext.workflow.model import WorkflowPackageState, WorkflowPackageRequest
import ckanext.workflow.logic.schema as workflow_schema
from ckanext.workflow.interface import IWorkflowPackageStateController
from ckanext.workflow.common import get_action, chained_action, model, side_effect_free
from ckanext.workflow.interface import IWorkflowPackageRequestController
from ckanext.workflow.model import WorkflowPackageRequest
import ckanext.workflow.logic.schema as workflow_schema
import ckanext.workflow.common as common
from ckanext.workflow.interface import IWorkflowPackageRequestController
from ckanext.workflow.model import WorkflowPackageRequest
import ckanext.workflow.logic.schema as workflow_schema
import ckanext.workflow.common as common
from ckanext.workflow.model import WorkflowPackageRequest, WorkflowPackageState
from ckan.plugins import toolkit
import ckanext.workflow.logic.schema as workflow_schema
from ckanext.workflow.model import WorkflowPackageRequest
from ckanext.workflow.interface import IWorkflowPackageRequestController
from ckan.plugins import PluginImplementations, toolkit
import ckanext.workflow.logic.schema as workflow_schema

log = common.getLogger(__name__)


@workflow_action_schema_decorator
def workflow_dataset_request_update(context, validated_data_dict):
    """Just some text"""
    workflow_dataset_request = WorkflowPackageRequest.update(context, validated_data_dict)
    for plugin in PluginImplementations(IWorkflowPackageRequestController):
        plugin.after_request_update(context, validated_data_dict)
    return workflow_dataset_request.as_dict()


@workflow_action_schema_decorator
def workflow_dataset_state_update(context, validated_data_dict):
    """Just some text"""
    print("workflow_dataset_state_update")
    session = context["session"]
    model = context["model"]
    user = context["user"]

    actor = model.User.by_name(user)

    log.warning("workflow_dataset_state_update validated_data_dict = [{}]".format(validated_data_dict))
    package_id, state_id = toolkit.get_or_bust(validated_data_dict, ['package_id', 'state_id'])

    # get the existing WorkflowPackageState (if exists)
    workflow_state = WorkflowPackageState.get(package_id)

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
                actor.id, package_id, activity_type,
                {'request': request.as_dict(), 'actor': actor.name if actor else None}
            )
            session.add(request_activity)
    else:
        workflow_state.state_id = state_id

    session.add(workflow_state)

    session.flush()

    if WorkflowBackend.get_state(state_id).dataset_fields:
        # make sure this patch will be ignored
        package_patch_context = dict(context, defer_commit=True, ignore_auth=True, ignore_workflow=True)
        package_patch_data_dict = dict(WorkflowBackend.get_state(state_id).dataset_fields, id=package_id)
        get_action('package_patch')(package_patch_context, package_patch_data_dict)

    session.flush()

    for plugin in PluginImplementations(IWorkflowPackageStateController):
        plugin.after_state_update(context, validated_data_dict)

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
    return pkg_dict


@workflow_action_schema_decorator
def workflow_dataset_request_create(context, validated_data_dict):
    """Just some text"""
    request = WorkflowPackageRequest.create(context, validated_data_dict)
    for plugin in common.PluginImplementations(IWorkflowPackageRequestController):
        plugin.after_request_create(context, validated_data_dict)
    return request.as_dict()


@side_effect_free
@workflow_action_schema_decorator
def workflow_dataset_request_show(context, validated_data_dict):
    """Just some text"""
    return WorkflowPackageRequest.get(validated_data_dict['id']).as_dict()


@side_effect_free
@workflow_action_schema_decorator
def workflow_dataset_request_list(context, validated_data_dict):
    """Just some text"""
    return [request.as_dict() for request in WorkflowPackageRequest.all()]


@workflow_action_schema_decorator
def workflow_dataset_request_delete(context, validated_data_dict):
    """Just some text"""
    log.warning(" workflow_dataset_request_delete")
    session = context["session"]
    model = context["model"]
    user = context["user"]

    actor = model.User.by_name(user)

    request_id = toolkit.get_or_bust(validated_data_dict, 'id')
    # get the existing WorkflowPackageState (if exists)
    workflow_dataset_request = WorkflowPackageRequest.get(request_id)

    session.delete(workflow_dataset_request)

    for plugin in PluginImplementations(IWorkflowPackageRequestController):
        plugin.after_request_delete(context, validated_data_dict)

    request_activity = model.Activity(
        actor.id, request_id, "deleted request",
        {'request': workflow_dataset_request.as_dict(), 'actor': actor.name if actor else None}
    )
    session.add(request_activity)

    if not context.get('defer_commit'):
        model.repo.commit()
