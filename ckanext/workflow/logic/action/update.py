from ckanext.workflow.plugin.interfaces import IWorkflowRequestController
from ckan.plugins import toolkit, PluginImplementations
import ckanext.workflow.helpers as helpers
import ckanext.workflow.constants as workflow_constants
from ckanext.workflow.plugin.interfaces import IWorkflowPackageStateController


def workflow_request_update(context, data_dict):
    """

    :param context:
    :param data_dict:
    """
    for plugin in PluginImplementations(IWorkflowRequestController):
        plugin.before_request_update(context, data_dict)
    for plugin in PluginImplementations(IWorkflowRequestController):
        plugin.after_request_update(context, data_dict)


def workflow_set_state(context, data_dict):
    """

    :param context:
    :param data_dict:
    :return:
    """
    id, state = toolkit.get_or_bust(data_dict, ['id', 'state'])
    from_state = helpers._get_state(id).label

    _state = workflow_constants.WORKFLOW.get_state(state)
    package_patch_dict = {
        'id': id,
        workflow_constants.DEFAULT_FIELD: state
    }
    if _state.dataset_fields:
        extras = _state.dataset_fields.pop('extras', [])
        package_patch_dict.update({f.get("key"): f.get("value") for f in extras})

    for plugin in PluginImplementations(IWorkflowPackageStateController):
        plugin.before_package_state_update(context, package_patch_dict)
    package_patch_dict = toolkit.get_action('package_patch')(dict(context, workflow_set_state=True), package_patch_dict)
    for plugin in PluginImplementations(IWorkflowPackageStateController):
        plugin.after_package_state_update(context, package_patch_dict)
    return package_patch_dict
