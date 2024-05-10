from typing import Optional
from ckanext.workflow.constants import DEFAULT_ROLES, DEFAULT_STATE, DEFAULT_STATES, DEFAULT_TRANSITIONS, \
    DEFAULT_UPDATE_ACTIONS
from ckanext.workflow.backend.schema import workflow_state_schema, workflow_transition_schema, \
    workflow_update_action_schema
from ckan.exceptions import CkanConfigurationException
from ckan.plugins import toolkit, PluginImplementations
from ckanext.workflow.common import model
from ckanext.workflow.plugins.interfaces import IWorkflow
from ckanext.workflow.backend import WorkflowState, WorkflowTransition
from ckan.logic.auth import get_package_object
# logging
import logging
log = logging.getLogger(__name__)

_check_access = toolkit.check_access
_NotAuthorized = toolkit.NotAuthorized
_ValidationError = toolkit.ValidationError
_navl_validate = toolkit.navl_validate
_g = toolkit.g


def get_context(for_view: Optional[bool] = None):
    _context = {
        'model': model,
        'session': model.Session,
        'user': _g.user,
        'for_view': True,
        'auth_user_obj': _g.userobj
    }
    if for_view is not None:
        _context['for_view'] = for_view
    return _context


def check_access(action, context, data_dict):
    """ Wrapper around the toolkit.check_access which will return False instead of a NotAuthorized """
    result = False
    try:
        result = _check_access(action, context, data_dict)
    except _NotAuthorized:
        pass
    return result


def show(pkg_dict, should_pkg_be_private, action, should_action_be_allowed, context=None):
    if context is None:
        context = get_context()
    return pkg_dict.get("private") == should_pkg_be_private and check_access(action, context,
                                                                             pkg_dict) == should_action_be_allowed


def get_roles(context):
    roles = DEFAULT_ROLES
    for plugin in PluginImplementations(IWorkflow):
        roles = plugin.get_roles(roles)
    return roles


def get_states(context, roles):
    states = DEFAULT_STATES
    for plugin in PluginImplementations(IWorkflow):
        states = plugin.get_states(states)

    # check if all id's are unique
    ids = [state.get("id", None) for state in states]
    if len(ids) > len(set(ids)):
        raise CkanConfigurationException("state_ids")

    # validate all states
    state_schema = workflow_state_schema(roles, ids)
    errors = {}
    result = []
    for state in states:
        state_dict, state_errors = _navl_validate(state, state_schema, context)
        if not state_errors:
            state_obj = WorkflowState(**dict(state_dict))
            result.append(state_obj)
        else:
            errors[state_dict.get("id", None)] = state_errors
    if errors:
        raise _ValidationError(errors, 'get_states_error_summary', 'get_states_extra_msg')
    return result


def get_default_state(context, states):
    default_state = DEFAULT_STATE
    for plugin in PluginImplementations(IWorkflow):
        default_state = plugin.get_default_state(default_state)
    if default_state is not None and not default_state in states:
        raise _ValidationError(default_state, 'get_states_error_summary', 'get_states_extra_msg')
    return default_state


def get_transitions(context, roles, states):
    transitions = DEFAULT_TRANSITIONS
    for plugin in PluginImplementations(IWorkflow):
        transitions = plugin.get_transitions(transitions)

    # check if all id's are unique
    transition_ids = [(transition.get("from_state", None), transition.get("to_state", None)) for transition in
                      transitions]
    if len(transition_ids) > len(set(transition_ids)):
        raise _ValidationError("transition_ids")

    # validate all transitions
    transition_schema = workflow_transition_schema(roles, states)
    errors = {}
    result = []
    for transition in transitions:
        transition_dict, transition_errors = _navl_validate(transition, transition_schema, context)
        if not transition_errors:
            result.append(WorkflowTransition(**transition_dict))
        else:
            errors[(transition_dict.get("from_state", None), transition_dict.get("to_state", None))] = transition_errors
    if errors:
        raise _ValidationError(errors, 'get_transitions_error_summary', 'get_transitions_extra_msg')

    return result


def default_getter(context, data_dict):
    pkg = get_package_object(context, data_dict)
    return pkg.id if pkg is not None else None


def get_update_actions():
    """

    :return:
    """

    update_actions = {update_action: default_getter for update_action in DEFAULT_UPDATE_ACTIONS}

    for plugin in PluginImplementations(IWorkflow):
        update_actions = plugin.get_update_actions(update_actions)

    # validate all transitions
    schema = workflow_update_action_schema()
    errors = {}
    for update_action in update_actions:
        action_getter = update_actions.get(update_action)
        if action_getter is None:
            action_getter = default_getter
            update_actions[update_action] = default_getter
        data = {'action': update_action, 'getter': update_actions.get(update_action)}
        _, update_action_errors = _navl_validate(data, schema, {})
        if update_action_errors:
            errors[update_action] = update_action_errors

    if errors:
        raise _ValidationError(errors, 'get_update_actions_error_summary', 'get_update_actions_extra_msg')

    if 'package_update' in update_actions:
        del update_actions['package_update']

    return update_actions
