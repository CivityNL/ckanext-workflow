from ckan.lib.search import index_for
from ckanext.workflow.backend import WorkflowBackend
from ckanext.workflow.logic import workflow_action_schema_decorator
from ckanext.workflow.interface import IWorkflowStateController
from ckanext.workflow.common import (
    get_action, side_effect_free, get_or_bust, PluginImplementations, getLogger, missing
)
from ckanext.workflow.model import WorkflowRequest, WorkflowState, WorkflowMessage
from ckanext.workflow.interface import IWorkflowRequestController
import ckan.lib.dictization.model_dictize as model_dictize
import ckanext.workflow.helpers as helpers
from ckanext.workflow.logic import DEFAULT_ACTIONS, OBJECT_TYPES

log = getLogger(__name__)

__all__ = [f'workflow_{o}_{a}' for a in DEFAULT_ACTIONS for o in OBJECT_TYPES]


# state related actions
@workflow_action_schema_decorator
def workflow_state_create(context, package_id, state_id):
    pass

@workflow_action_schema_decorator
def workflow_state_update(context, package_id, state_id):
    session = context["session"]
    model = context["model"]
    user = context["user"]

    actor = model.User.by_name(user)

    # get the existing WorkflowState (if exists)
    workflow_state = WorkflowState.get(package_id)

    prev_state = None
    if workflow_state is not None:
        prev_state = workflow_state.state_id

    # stop handling this on a non-update
    if prev_state == state_id:
        return workflow_state.as_dict() if workflow_state is not None else None

    # create or update the WorkflowState (if exists)
    if workflow_state is None:
        workflow_state = WorkflowState(package_id, state_id)
        activity_type = "created state"
    else:
        workflow_state.state_id = state_id
        activity_type = "updated state"

    session.add(workflow_state)

    requests = WorkflowRequest.get_for_package(package_id)
    for request in requests:
        if request.is_open:
            activity_type = "updated request"
            request.set_deleted(actor.id)
            if request.request_state == state_id:
                request.set_resolved(actor.id)
            session.add(request)
            request_activity = model.Activity(
                actor.id, request.id, activity_type,
                {'request': request.as_dict(), 'actor': actor.name if actor else None}
            )
            session.add(request_activity) 

    session.flush()

    dataset_fields = WorkflowBackend.get_dataset_fields_for_state(state_id)
    print(f"dataset_fields: {dataset_fields}")
    if dataset_fields:
        # make sure this patch will be ignored
        package_patch_context = dict(context, defer_commit=True, ignore_auth=True, ignore_workflow=True)
        package_patch_data_dict = dict(dataset_fields, id=package_id)
        get_action('package_patch')(package_patch_context, package_patch_data_dict)
        for obj in [obj for obj in session.new if isinstance(obj, model.Activity) and obj.object_id == package_id]:
            session.expunge(obj)

    session.flush()

    for plugin in PluginImplementations(IWorkflowStateController):
        plugin.after_state_update(context, package_id, state_id)

    # Create activity
    pkg_dict = get_action('package_show')(context, {'id': package_id})

    activity = model.Activity(
        actor.id, package_id, activity_type, {'package': pkg_dict, 'actor': actor.name if actor else None}
    )
    session.add(activity)

    if not context.get('defer_commit'):
        model.repo.commit()

    # update the SOLR index
    index = index_for(model.Package)
    pkg_dict = get_action('package_show')(context, {'id': package_id})
    index.update_dict(pkg_dict)

    # return the SOLR index
    return pkg_dict


@workflow_action_schema_decorator
def workflow_state_patch(context, package_id, state_id):
    return workflow_state_update(context, package_id, state_id)


@workflow_action_schema_decorator
def workflow_state_delete(context, package_id):
    pass


@workflow_action_schema_decorator
def workflow_state_purge(context, package_id):
    pass


@workflow_action_schema_decorator
def workflow_state_show(context, package_id):
    return WorkflowState.get(package_id).as_dict()


@workflow_action_schema_decorator
def workflow_state_list(context, validated_data_dict,
                        limit=missing, offset=missing, 
                        order_by=missing, 
                        created_from=missing, created_to=missing, modified_from=missing, modified_to=missing, 
                        state=missing, owner_org=missing, package_state=missing
    ):
    return [r.as_dict(context) for r in WorkflowState.query(**validated_data_dict).all()]

# request related actions

@workflow_action_schema_decorator
def workflow_request_create(context, validated_data_dict):
    """Just some text"""
    print(f"workflow_dataset_request_create -> {validated_data_dict}")
    request_message = None
    if 'request_message' in validated_data_dict and validated_data_dict['request_message']:
        request_message = validated_data_dict.pop('request_message')

    current_state = helpers._get_state_id(validated_data_dict['package_id'])

    request = WorkflowRequest.create(
        dict(context, defer_commit=request_message is not None),
        dict(validated_data_dict, current_state=current_state)
    )
    if request_message:
        WorkflowMessage.create(context, {
            'workflow_request_id': request.id, 
            'user_id': request.request_user_id,
            'content': request_message
        }
        )
    for plugin in PluginImplementations(IWorkflowRequestController):
        plugin.after_request_create(context, validated_data_dict)
    print(f"workflow_dataset_request_create -> return request as dict")
    return request.as_dict()

@workflow_action_schema_decorator
def workflow_request_update(context, validated_data_dict):
    '''
    workflow_dataset_request_update ... should add some text here


    :param context: param
    :type context: type
    :param validated_data_dict: param
    :type validated_data_dict: type
    :return: return
    :rtype: return

    '''
    workflow_dataset_request = WorkflowRequest.update(context, validated_data_dict)
    for plugin in PluginImplementations(IWorkflowRequestController):
        plugin.after_request_update(context, validated_data_dict)
    return workflow_dataset_request.as_dict()

@workflow_action_schema_decorator
def workflow_request_patch(context, validated_data_dict):
    return workflow_request_update(context, validated_data_dict)

@workflow_action_schema_decorator
def workflow_request_delete(context, validated_data_dict):
    """Just some text"""
    log.warning(" workflow_dataset_request_delete")
    session = context["session"]
    model = context["model"]
    user = context["user"]

    actor = model.User.by_name(user)

    request_id = get_or_bust(validated_data_dict, 'id')
    # get the existing WorkflowState (if exists)
    workflow_dataset_request = WorkflowRequest.get(request_id)

    session.delete(workflow_dataset_request)

    for plugin in PluginImplementations(IWorkflowRequestController):
        plugin.after_request_delete(context, validated_data_dict)

    request_activity = model.Activity(
        actor.id, request_id, "deleted request",
        {'request': workflow_dataset_request.as_dict(), 'actor': actor.name if actor else None}
    )
    session.add(request_activity)

    if not context.get('defer_commit'):
        model.repo.commit()

@workflow_action_schema_decorator
def workflow_request_purge(context, validated_data_dict):
    pass

@workflow_action_schema_decorator
def workflow_request_show(context, validated_data_dict):
    """Just some text"""
    return WorkflowRequest.get(validated_data_dict['id']).as_dict()

@workflow_action_schema_decorator
def workflow_request_list(context, validated_data_dict):
    """Just some text"""
    return [request.as_dict() for request in WorkflowRequest.all()]

# message related actions


@workflow_action_schema_decorator
def workflow_message_create(context, validated_data_dict,
                            created=missing,
        modified=missing,
        state=missing,
        user_id=missing,
        content=missing,
        reference_type=missing,
        reference_id=missing
                            ):
    return WorkflowMessage.create(context, validated_data_dict).as_dict(context)

@workflow_action_schema_decorator
def workflow_message_update(context, validated_data_dict, id,
                            created=missing,
        modified=missing,
        state=missing,
        user_id=missing,
        content=missing,
        reference_type=missing,
        reference_id=missing):
    return WorkflowMessage.update(context, validated_data_dict).as_dict(context)

@workflow_action_schema_decorator
def workflow_message_patch(context, validated_data_dict,
        created=missing,
        modified=missing,
        state=missing,
        user_id=missing,
        content=missing,
        reference_type=missing,
        reference_id=missing):
  return workflow_message_update(**locals())

@workflow_action_schema_decorator
def workflow_message_delete(context, validated_data_dict, id):
  return WorkflowMessage.delete(context, validated_data_dict).as_dict(context)

@workflow_action_schema_decorator
def workflow_message_purge(context, validated_data_dict, id):
  return WorkflowMessage.purge(context, validated_data_dict).as_dict(context)

@side_effect_free
@workflow_action_schema_decorator
def workflow_message_show(context, validated_data_dict, id):
  return WorkflowMessage.get(id).as_dict(context)

@side_effect_free
@workflow_action_schema_decorator
def workflow_message_list(context, validated_data_dict, **kwargs):
  order_by = validated_data_dict.get('order_by', None)
  paginate_kwargs = {k: v for k,v in validated_data_dict.items() if k in ['limit', 'offset']}
  filter_kwargs = {k: v for k,v in validated_data_dict.items() if not k.startswith('facet') and k not in ['limit', 'offset', 'order_by']}
  result = {}
  result['count'] = WorkflowMessage.query(order_by=order_by, **filter_kwargs).count()
  if validated_data_dict.get('facet'):
      facet_kwargs = {
          'fields': validated_data_dict.get('facet_field'),
          'limit': validated_data_dict.get('facet_limit'),
          'min_count': validated_data_dict.get('facet_mincount')
      }
      result['facets'] = WorkflowMessage.facet(**facet_kwargs, **filter_kwargs).all()
  result['parameters'] = validated_data_dict
  result['results'] = [r.as_dict(context) for r in WorkflowMessage.query(**paginate_kwargs, order_by=order_by, **filter_kwargs).all()]
  return result

###########################################
###########################################
###########################################
###########################################


@workflow_action_schema_decorator
def workflow_dataset_request_message_create(context, validated_data_dict):
    """Just some text"""
    print(f"workflow_dataset_request_create -> {validated_data_dict}")
    request = WorkflowMessage.create(context, validated_data_dict)
    print(f"workflow_dataset_request_create -> return request as dict")
    return request.as_dict()



@workflow_action_schema_decorator
def workflow_dataset_request_delete(context, validated_data_dict):
    """Just some text"""
    log.warning(" workflow_dataset_request_delete")
    session = context["session"]
    model = context["model"]
    user = context["user"]

    actor = model.User.by_name(user)

    request_id = get_or_bust(validated_data_dict, 'id')
    # get the existing WorkflowState (if exists)
    workflow_dataset_request = WorkflowRequest.get(request_id)

    session.delete(workflow_dataset_request)

    for plugin in PluginImplementations(IWorkflowRequestController):
        plugin.after_request_delete(context, validated_data_dict)

    request_activity = model.Activity(
        actor.id, request_id, "deleted request",
        {'request': workflow_dataset_request.as_dict(), 'actor': actor.name if actor else None}
    )
    session.add(request_activity)

    if not context.get('defer_commit'):
        model.repo.commit()


@side_effect_free
@workflow_action_schema_decorator
def workflow_request_activity_list(context, validated_data_dict):
    print(f"workflow_request_activity_list -> {validated_data_dict}")
    validated_data_dict['include_data'] = False
    include_hidden_activity = validated_data_dict.get('include_hidden_activity', False)

    offset = validated_data_dict.get('offset', None)
    limit = validated_data_dict.get('limit', None)

    request_id = validated_data_dict.get('id')
    request = WorkflowRequest.get(request_id)

    activities = request.get_activities(limit=limit, offset=offset)
    return model_dictize.activity_list_dictize(
        activities, context, include_data=validated_data_dict['include_data']
    )


@side_effect_free
@workflow_action_schema_decorator
def workflow_request_message_list(context, validated_data_dict):
    request_id = validated_data_dict.get('id')
    request = WorkflowRequest.get(request_id)
    return [dict(m.as_dict()) for m in request.messages] if request else []
