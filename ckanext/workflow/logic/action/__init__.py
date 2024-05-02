from ckan.plugins import toolkit
from ckanext.workflow.helpers import _get_state
import ckanext.workflow.logic.action.get as get
import ckanext.workflow.logic.action.create as create
import ckanext.workflow.logic.action.update as update
import ckanext.workflow.logic.action.delete as delete


'''API functions for deleting data from CKAN.'''


def workflow_set_state_after_update(action, getter, context, data_dict):
    """

    :param action:
    :param getter:
    :param context:
    :param data_dict:
    :return:
    """
    result = None
    package_ids = getter(context, data_dict)
    if 'workflow_set_state' in context:
        print(
            f"workflow_set_state_after_update context[workflow_set_state] = {context.get('workflow_set_state', None)} {context['workflow_set_state']}")
    else:
        print("workflow_set_state_after_update 'workflow_set_state' NOT IN CONTEXT")
    if package_ids and not context.get("workflow_set_state", False):
        package_ids = package_ids if isinstance(package_ids, list) else [package_ids]
        result = []
        for package_id in package_ids:
            pkg_dict = toolkit.get_action('package_show')(context, {"id": package_id})
            state = _get_state(pkg_dict)
            state_on_update = state.state_on_update(action, context, pkg_dict)
            set_state_result = None
            if state.id != state_on_update:
                set_state_dict = {"id": package_id, "state": state_on_update}
                set_state_result = toolkit.get_action('workflow_set_state')(context, set_state_dict)
            result.append(set_state_result)
    if result is not None and len(result) == 1:
        result = result[0]
    return result


def workflow_chained_action(action, getter):
    @toolkit.chained_action
    def chained_action(original_action, context, data_dict):
        original_result = original_action(context, data_dict)
        if not context.get("workflow_set_state", False):
            set_state_result = workflow_set_state_after_update(action, getter, context, data_dict)
            if set_state_result is not None:
                return set_state_result
        return original_result

    return chained_action
