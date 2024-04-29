from ckanext.workflow.plugin.interfaces import IWorkflowPackageStateController, IWorkflowRequestController
from ckan.plugins import toolkit, PluginImplementations
import ckanext.workflow.constants as workflow_constants


tk_chained_action = toolkit.chained_action


@tk_chained_action
def package_update(original_action, context, data_dict):
    print("chained_action package_update")
    return original_action(context, data_dict)


def workflow_request_update(context, data_dict):
    plugin: IWorkflowRequestController
    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.before_request_update(context, data_dict)
    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.after_request_update(context, data_dict)


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
