from ckan.plugins import toolkit
from ckanext.workflow.helpers import _get_state
from ckan.logic.auth import get_package_object

import ckanext.workflow.logic.auth.get as get
import ckanext.workflow.logic.auth.create as create
import ckanext.workflow.logic.auth.update as update
import ckanext.workflow.logic.auth.delete as delete

tk_chained_auth_function = toolkit.chained_auth_function
tk__ = toolkit._


def workflow_chained_auth_function(action, getter):
    
    @tk_chained_auth_function
    def chained_auth_action(original_action, context, data_dict):
        print(f"chained_auth_action {action}")
        original_result = original_action(context, data_dict)
        original_success = original_result.get("success")
        result = original_result
        if not original_success:
            result = original_result
        elif context.get("workflow_auth_checked", False):
            print(f"chained_auth_action {action} workflow_auth_checked = {context.get('workflow_auth_checked', False)}")
        else:
            package_ids = getter(context, data_dict)
            if not package_ids:
                return original_action(context, data_dict)
            package_ids = package_ids if isinstance(package_ids, list) else [package_ids]
            for package_id in package_ids:
                pkg = get_package_object({}, {"id": package_id})
                user = context["user"]
                state = _get_state(pkg)
                success = state.update_allowed(context, user, pkg.id, pkg.owner_org)
                context["workflow_auth_checked"] = True
                result = {"success": success}
                if not success:
                    user = context["user"]
                    result['msg'] = tk__('[WORKFLOW] User %s not authorized to edit these packages') % user
                    break
        return result

    return chained_auth_action
