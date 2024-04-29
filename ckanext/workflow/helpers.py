# encoding: utf-8

'''Helper functions.'''

from ckanext.workflow import utils
import ckanext.workflow.constants as workflow_constants
from ckan.model import Package
from ckan.logic.auth import get_package_object


def show_notice_to_be_unpublished_on_edit(pkg_dict):
    return utils.show(pkg_dict, False, 'workflow_package_publish', False)


def get_state_label(pkg_dict):
    return _get_state(pkg_dict).label


def get_state_id(pkg_dict):
    return _get_state(pkg_dict).id


def _get_state(pkg):
    result = workflow_constants.WORKFLOW.get_state(None)
    if isinstance(pkg, dict):
        result = _get_state_pkg_dict(pkg)
    elif isinstance(pkg, Package):
        result = _get_state_pkg(pkg)
    else:
        result = _get_state_pkg_id(pkg)        
    return result

def _get_state_pkg_id(pkg_id):
    return _get_state_pkg(Package.get(pkg_id))


def _get_state_pkg_dict(pkg_dict):
    result = None
    field = workflow_constants.DEFAULT_FIELD
    if field in pkg_dict:
        result = pkg_dict.get(field)
    elif 'extras' in pkg_dict:
        extra = next((extra for extra in pkg_dict.get("extras") if extra.get("key") == field), {})
        result = extra.get("value", None)
    return workflow_constants.WORKFLOW.get_state(result)


def _get_state_pkg(pkg):
    field = workflow_constants.DEFAULT_FIELD
    result = pkg.extras.get(field, None) if pkg.extras else None
    return workflow_constants.WORKFLOW.get_state(result)


def get_allowed_states(pkg_dict):
    context = utils.get_context()
    state = _get_state(pkg_dict)
    user_id = context.get("user", None)
    pkg_id = pkg_dict.get("id", None)
    org_id = pkg_dict.get("owner_org", None)
    result = {"request": [], "approve": [], "assign": []}
    for action in result:
        result[action] = workflow_constants.WORKFLOW.allowed_states(context, state.id, user_id, pkg_id, org_id, action)
    return result
