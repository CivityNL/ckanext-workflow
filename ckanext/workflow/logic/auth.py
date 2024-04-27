from ckanext.workflow import utils
from ckan.plugins import toolkit
import ckanext.workflow.constants as workflow_constants

_ = toolkit._


@toolkit.auth_sysadmins_check
def package_set_state(context, data_dict):
    print(f"auth package_set_state data_dict = {data_dict}")
    pkg_dict = toolkit.get_action("package_show")(context, {"id": data_dict.get("id")})
    state_id = pkg_dict.get(workflow_constants.DEFAULT_FIELD, workflow_constants.DEFAULT_STATE)
    user_id = context.get("user", None)
    pkg_id = pkg_dict.get("id", None)
    org_id = pkg_dict.get("owner_org", None)
    if data_dict.get("state") not in workflow_constants.WORKFLOW.allowed_states(context, state_id, user_id, pkg_id, org_id, "assign"):
        return {"success": False}
    return {"success": True}
