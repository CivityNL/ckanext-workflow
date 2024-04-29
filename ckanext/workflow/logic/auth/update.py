from ckan.plugins import toolkit
import ckanext.workflow.constants as workflow_constants
from ckanext.workflow.helpers import _get_state, get_state_id
from ckan.logic.auth import get_package_object, get_user_object

tk_chained_auth_function = toolkit.chained_auth_function
tk_auth_sysadmins_check = toolkit.auth_sysadmins_check
tk_get_or_bust = toolkit.get_or_bust
tk__ = toolkit._
tk_get_action = toolkit.get_action


@tk_chained_auth_function
@tk_auth_sysadmins_check
def package_update(original_action, context, data_dict=None):
    print(f"chained_auth_function package_update")
    result = original_action(context, data_dict)
    if result.get("success"):
        pkg = get_package_object(context, data_dict)
        user = context["user"]
        state = _get_state(pkg)
        success = state.update_allowed(context, user, pkg.id, pkg.owner_org)
        result = {"success": success}
        if not success:
            result['msg'] = tk__('[WORKFLOW] User %s not authorized to edit these packages') % user
    return result


@tk_auth_sysadmins_check
def package_set_state(context, data_dict):
    print(f"auth package_set_state data_dict = {data_dict}")
    pkg_id, state = tk_get_or_bust(data_dict, ['id', 'state'])
    result = {"success": True}
    pkg_dict = tk_get_action("package_show")(context, {"id": data_dict.get("id")})
    state_id = get_state_id(pkg_dict)
    user_id = context.get("user", None)
    pkg_id = pkg_dict.get("id", None)
    org_id = pkg_dict.get("owner_org", None)
    allowed_states = workflow_constants.WORKFLOW.allowed_states(context, state_id, user_id, pkg_id, org_id, "assign")
    if data_dict.get("state") not in allowed_states:
        result = {"success": False}
    context["workflow_auth_checked"] = True
    return result
