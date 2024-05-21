# encoding: utf-8

'''Helper functions.'''

from typing import List

from ckanext.workflow import utils
import ckanext.workflow.constants as workflow_constants
from ckan.plugins import toolkit
from ckanext.workflow.common import model

# logging
import logging
log = logging.getLogger(__name__)

convert_package_name_or_id_to_id = toolkit.get_converter('convert_package_name_or_id_to_id')


def show_notice_to_be_unpublished_on_edit(pkg_dict):
    return True


def get_state_label(pkg_dict):
    return _get_state(pkg_dict).label


def get_state_id(pkg_dict):
    return _get_state(pkg_dict).id


def _get_state(pkg):
    result = workflow_constants.WORKFLOW.get_state(None)
    if isinstance(pkg, dict):
        result = _get_state_pkg_dict(pkg)
    elif isinstance(pkg, model.Package):
        result = _get_state_pkg(pkg)
    elif pkg is not None:
        result = _get_state_pkg_id(pkg)
    return result


def _get_state_pkg_id(pkg_id: str):
    return _get_state_pkg(model.Package.get(pkg_id))


def _get_state_pkg_dict(pkg_dict: dict):
    result = None
    field = workflow_constants.DEFAULT_FIELD
    if field in pkg_dict:
        result = pkg_dict.get(field)
    elif 'extras' in pkg_dict:
        extra = next((extra for extra in pkg_dict.get("extras") if extra.get("key") == field), {})
        result = extra.get("value", None)
    return workflow_constants.WORKFLOW.get_state(result)


def _get_state_pkg(pkg: model.Package):
    if pkg is None:
        return None
    field = workflow_constants.DEFAULT_FIELD
    result = pkg.extras.get(field, None) if pkg.extras else None
    return workflow_constants.WORKFLOW.get_state(result)


def get_allowed_states(pkg_dict):
    context = utils.get_context()
    pkg_id = pkg_dict.get("id", None)
    state = _get_state(pkg_id)
    user_id = context.get("user", None)
    org_id = pkg_dict.get("owner_org", None)
    result = {"request": [], "approve": [], "assign": []}
    for action in result:
        result[action] = workflow_constants.WORKFLOW.allowed_states(context, state.id, user_id, pkg_id, org_id, action)
    return result


def workflow_choices_helper(field: dict) -> List[dict[str, str]]:
    """
    This helper function will return a list of allowed workflow states for a given dataset.

    :param field:
    :return:
    """

    # we'll assume this is only called

    user = toolkit.g.userobj
    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.g.user,
        'for_view': True,
        'auth_user_obj': user
    }

    # check if pkg is already defined in the global
    pkg = getattr(toolkit.g, 'pkg', None)
    # if not try to get it from either the view_args (view) or the payload (action)
    if pkg is None:
        data_dict = None
        if "logic_function" in toolkit.request.view_args:
            data_dict = toolkit.request.get_json()
        elif "id" in toolkit.request.view_args:
            data_dict = toolkit.request.view_args

        try:
            pkg = get_package_object(context=context, data_dict=data_dict)
        except (toolkit.ObjectNotFound, toolkit.ValidationError) as e:
            pass
        except Exception as e:
            pass

    #
    if pkg is None:
        result = [
            {
                "value": workflow_constants.WORKFLOW.default_state.id,
                "label": workflow_constants.WORKFLOW.default_state.id
            }
        ]
    else:
        state = _get_state_pkg(pkg)
        if state is None:
            state = workflow_constants.WORKFLOW.default_state

        allowed_states = [state.id] + workflow_constants.WORKFLOW.allowed_states(context, state.id, user.id, pkg.id, pkg.owner_org, "assign")
        result = [{"value": state, "label": state} for state in allowed_states]

    return result


def workflow_enabled_for_organization(organization):
    """

    :param organization:
    :return:
    """
    return True
