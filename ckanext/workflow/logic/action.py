from ckanext.workflow.logic.interface import IWorkflowPackageStateController, IWorkflowRequestController
from ckan.plugins import toolkit, PluginImplementations
from ckanext.workflow.model import WorkflowRequest
import ckanext.workflow.logic.schema as workflow_schema
import ckanext.workflow.constants as workflow_constants
from ckan.plugins import toolkit
import ckanext.workflow.constants as workflow_constants
from ckanext.workflow.helpers import _get_state, get_state_id
from ckan.logic.auth import get_package_object, get_user_object


'''API functions for deleting data from CKAN.'''

@toolkit.side_effect_free
def workflow_request_show(context, data_dict):
	### based on an ID, return the request
    request_id = toolkit.get_or_bust(data_dict, 'id')
    request = WorkflowRequest.get(request_id)
    if not request:
        raise toolkit.ObjectNotFound
    return request.as_dict()


@toolkit.side_effect_free
def workflow_request_list(context, data_dict):
	### based on query parameters, return the requests
	return [request.as_dict() for request in WorkflowRequest.all()]


def workflow_request_create(context, data_dict):
	###
    print(f"workflow_request_create with {data_dict}")
    model = context["model"]
    session = context["session"]
    user = context["user"]

    # fill 
    if 'request_user_id' not in data_dict or not data_dict['request_user_id']:
         data_dict['request_user_id'] = user

    schema = workflow_schema.workflow_request_create_schema()

    request_dict, errors = toolkit.navl_validate(data_dict, schema, context)
    if errors:
        session.rollback()
        raise toolkit.ValidationError(errors)

    plugin: IWorkflowRequestController
    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.before_request_create(context, request_dict)

    request = WorkflowRequest(**request_dict)
    request.save()

    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.after_request_create(context, request_dict)
    return request.as_dict()
	


def workflow_request_update(context, data_dict):
    plugin: IWorkflowRequestController
    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.before_request_update(context, data_dict)
    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.after_request_update(context, data_dict)



def workflow_request_delete(context, data_dict):
    plugin: IWorkflowRequestController
    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.before_request_delete(context, data_dict)
    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.after_request_delete(context, data_dict)


def workflow_request_purge(context, data_dict):
    plugin: IWorkflowRequestController
    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.before_request_purge(context, data_dict)
    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.after_request_purge(context, data_dict)


def package_set_state(context, data_dict):
    print(f"package_set_state {data_dict}")
    id, state = toolkit.get_or_bust(data_dict, ['id', 'state'])
    
    toolkit.check_access('workflow_package_set_state', context, data_dict)

    _state = workflow_constants.WORKFLOW.get_state(state)
    package_patch_dict = {
         'id': id,
         workflow_constants.DEFAULT_FIELD: state,
         'extras': [{
              "key": workflow_constants.DEFAULT_FIELD,
              "value": state
         }]
    }
    if _state.dataset_fields:
        extras = _state.dataset_fields.pop('extras', [])
        package_patch_dict.update(_state.dataset_fields)
        package_patch_dict['extras'].extend([extra for extra in extras if extra.get("key") != workflow_constants.DEFAULT_FIELD])
    print(f"package_set_state package_patch {package_patch_dict}")
    context["workflow_ignore"] = True
    plugin: IWorkflowPackageStateController
    for plugin in PluginImplementations(IWorkflowPackageStateController):
         plugin.before_package_state_update(context, package_patch_dict)
    package_patch_dict = toolkit.get_action('package_patch')(context, package_patch_dict)
    for plugin in PluginImplementations(IWorkflowPackageStateController):
         plugin.after_package_state_update(context, package_patch_dict)
    return package_patch_dict


def workflow_chained_action(action, getter):
    @toolkit.chained_action
    def chained_action(original_action, context, data_dict):
        print(f"workflow_chained_action chained_action {action}")
        original_result = original_action(context, data_dict)
        package_ids = getter(context, data_dict)
        if not package_ids or context.get("workflow_ignore", False):
            print(f"returning original result based on package_ids = {package_ids} and workflow_ignore = {context.get('workflow_ignore', False)}")
            return original_result
        package_ids = package_ids if isinstance(package_ids, list) else [package_ids]
        for package_id in package_ids:
            print(f"workflow_chained_action chained_action for {package_id}")
            pkg_dict = toolkit.get_action('package_show')(context, {"id": package_id})
            print(f"workflow_chained_action chained_action for {pkg_dict}")
            state = _get_state(pkg_dict)
            state_on_update = state.state_on_update(action, context, pkg_dict)
            print(f"workflow_chained_action chained_action for {package_id} is {state.id} vs {state_on_update}")
            if state.id != state_on_update:
                 toolkit.get_action('workflow_package_set_state')(context, {"id": package_id, "state": state_on_update})
        return original_result

    return chained_action

