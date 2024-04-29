from ckan.plugins import toolkit
from ckanext.workflow.helpers import _get_state
import ckanext.workflow.logic.action.get as get
import ckanext.workflow.logic.action.create as create
import ckanext.workflow.logic.action.update as update
import ckanext.workflow.logic.action.delete as delete


'''API functions for deleting data from CKAN.'''


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
