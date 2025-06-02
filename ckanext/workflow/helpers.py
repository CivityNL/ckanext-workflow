# encoding: utf-8

'''Helper functions.'''

from typing import List

from ckanext.workflow import utils
from ckanext.workflow.backend import WorkflowBackend
import ckanext.workflow.constants as workflow_constants
from ckan.plugins import toolkit
from ckanext.workflow.common import (
    model, get_package_object, convert_user_name_or_id_to_id, h, config, convert_package_name_or_id_to_id
)
from ckanext.workflow.model import WorkflowPackageState, WorkflowPackageRequest

# logging
import logging
log = logging.getLogger(__name__)


def show_notice_to_be_unpublished_on_edit(pkg_dict):
    return True


def get_state_label(pkg_dict):
    state = _get_state(pkg_dict)
    return state.label if state else None


def get_state_id(pkg_dict):
    state = _get_state(pkg_dict)
    return state.id if state else None


def _get_state(pkg):
    package_id = pkg
    if isinstance(pkg, dict):
        package_id = pkg.get("id")
    elif isinstance(pkg, model.Package):
        package_id = pkg.id
    else:
        package_id = convert_package_name_or_id_to_id(pkg, {'session': model.Session})
    state = WorkflowPackageState.get(package_id)
    return WorkflowBackend.get_state(state.state_id if state else None)


def get_allowed_states(pkg_dict):
    context = utils.get_context()
    pkg_id = pkg_dict.get("id", None)
    state = _get_state(pkg_id)
    user_id = convert_user_name_or_id_to_id(context.get("user", None), context)
    org_id = pkg_dict.get("owner_org", None)
    result = {"request": [], "approve": [], "assign": []}
    for action in result:
        result[action] = WorkflowBackend.allowed_states(context, state.id if state else None, user_id, pkg_id, org_id,
                                                        action)
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
                "value": WorkflowBackend.default_state.id,
                "label": WorkflowBackend.default_state.id
            }
        ]
    else:
        state = _get_state(pkg)
        if state is None:
            state = WorkflowBackend.default_state

        allowed_states = [state.id] + WorkflowBackend.allowed_states(context, state.id, user.id, pkg.id, pkg.owner_org, "assign")
        result = [{"value": state, "label": state} for state in allowed_states]

    return result


def package_request_count(package_id):
    return WorkflowPackageRequest.count_for_package(package_id)


# copied from ckanext-scheming
def language_text(text, prefer_lang=None):
    """
    :param text: {lang: text} dict or text string
    :param prefer_lang: choose this language version if available

    Convert "language-text" to users' language by looking up
    languag in dict or using gettext if not a dict
    """

    if prefer_lang is None:
        try:
            prefer_lang = h.lang()
        except TypeError:
            pass  # lang() call will fail when no user language available

    # list of keys to look for in order of importance
    lang_keys = [prefer_lang, config.get('ckan.locale_default', 'en'), sorted(text.keys())[0]]
    return next((text[lang_key] for lang_key in lang_keys if lang_key in text), '')
