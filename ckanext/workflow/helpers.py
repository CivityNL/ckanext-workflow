from ckanext.workflow import utils
import ckanext.workflow.constants as workflow_constants


def show_notice_to_be_unpublished_on_edit(pkg_dict):
    return utils.show(pkg_dict, False, 'workflow_package_publish', False)


def get_state_label(pkg_dict):
    return workflow_constants.WORKFLOW.get_state(get_state(pkg_dict)).label


def get_state(pkg_dict):
    result = None
    field = workflow_constants.DEFAULT_FIELD
    if field in pkg_dict:
        result = pkg_dict.get(field)
    elif 'extras' in pkg_dict:
        extra = next((extra for extra in pkg_dict.get("extras") if extra.get("key") == field), None)
        if extra:
            result = extra.get("value")
    if not workflow_constants.WORKFLOW.get_state(result):
        result = workflow_constants.DEFAULT_STATE
    return result


def get_allowed_states(pkg_dict):
    context = utils.get_context()
    state_id = get_state(pkg_dict)
    user_id = context.get("user", None)
    pkg_id = pkg_dict.get("id", None)
    org_id = pkg_dict.get("owner_org", None)
    result = {"request": [], "approve": [], "assign": []}
    for action in result:
        result[action] = workflow_constants.WORKFLOW.allowed_states(context, state_id, user_id, pkg_id, org_id, action)
    return result
