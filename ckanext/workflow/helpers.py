# encoding: utf-8

'''Helper functions.'''

from typing import List

from ckanext.workflow import utils
from ckanext.workflow.backend import WorkflowBackend
from ckan.plugins import toolkit
from ckanext.workflow.common import (
    model, get_package_object, convert_user_name_or_id_to_id, h, config, convert_package_name_or_id_to_id
)
from ckanext.workflow.model import WorkflowState, WorkflowRequest

# logging
import logging
log = logging.getLogger(__name__)


def show_notice_to_be_unpublished_on_edit(pkg_dict):
    return True


def get_transition_label(from_state, to_state):
    return WorkflowBackend.get_transition_label(from_state, to_state)


def get_state_label(pkg_dict):
    state_id = _get_state_id(pkg_dict)
    return WorkflowBackend.get_state_label(state_id)


def _get_state_id(pkg):
    package_id = pkg
    if isinstance(pkg, dict):
        package_id = pkg.get("id")
    elif isinstance(pkg, model.Package):
        package_id = pkg.id
    else:
        package_id = convert_package_name_or_id_to_id(pkg, {'session': model.Session})
    state = WorkflowState.get(package_id)
    return WorkflowBackend.get_state_id(state.state_id if state else None)


def get_allowed_states(pkg_dict):
    context = utils.get_context()
    pkg_id = pkg_dict.get("id", None)
    state_id = _get_state_id(pkg_id)
    user_id = convert_user_name_or_id_to_id(context.get("user", None), context)
    org_id = pkg_dict.get("owner_org", None)
    result = {"request": [], "approve": [], "assign": []}
    for action in result:
        result[action] = WorkflowBackend.allowed_states(context, state.id if state else None, user_id, pkg_id, org_id,
                                                        action)
    return result


def get_allowed_transitions(pkg_dict, action=None):
    context = utils.get_context()
    pkg_id = pkg_dict.get("id", None)
    state_id = _get_state_id(pkg_id)
    user_id = convert_user_name_or_id_to_id(context.get("user", None), context)
    org_id = pkg_dict.get("owner_org", None)
    return WorkflowBackend.allowed_transitions(context, state_id, user_id, pkg_id, org_id, action)


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
                "value": WorkflowBackend.default_state.id,
                "label": WorkflowBackend.default_state.id
            }
        ]
    else:
        state_id = _get_state_id(pkg)
        allowed_states = [state_id] + WorkflowBackend.allowed_states(context, state_id, user.id, pkg.id, pkg.owner_org, "assign")
        result = [{"value": state, "label": state} for state in allowed_states]

    return result


def package_request_count(package_id):
    return WorkflowRequest.count_for_package(package_id)

def get_states(): 
    return WorkflowBackend.get_states()

def get_transitions():
    return WorkflowBackend.get_transitions()