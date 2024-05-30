from typing import Callable, Dict, List

from ckanext.workflow.backend.classes import WorkflowState, WorkflowTransition
from ckanext.workflow.backend.schema import workflow_state_schema, workflow_transition_schema, \
    workflow_update_action_schema
import ckanext.workflow.constants as workflow_constants
from ckan.authz import is_sysadmin
import ckanext.workflow.common as common
from ckanext.authorization.backend import AuthorizationBackend

# logging
import logging

from ckanext.workflow.interface import IWorkflow

log = logging.getLogger(__name__)


def setup_states(update_actions, permissions):
    get_states = workflow_constants.DEFAULT_STATES
    for plugin in common.PluginImplementations(IWorkflow):
        get_states = plugin.get_states(get_states)

    # check if all id's are unique
    ids = [state.get("id", None) for state in get_states]
    if len(ids) > len(set(ids)):
        raise common.ValidationError("state_ids")

    # validate all states
    state_schema = workflow_state_schema(update_actions, permissions, ids)
    errors = {}
    result = []
    for state in get_states:
        state_dict, state_errors = common.navl_validate(state, state_schema, {})
        if not state_errors:
            result.append(state_dict)
        else:
            errors[state_dict.get("id", None)] = state_errors
    if errors:
        raise common.ValidationError(errors, 'get_states_error_summary', 'get_states_extra_msg')
    return result


def setup_default_state(states):
    result = workflow_constants.DEFAULT_STATE
    for plugin in common.PluginImplementations(IWorkflow):
        result = plugin.get_default_state(result)
    if result is not None and not result in states:
        raise common.ValidationError(result, 'get_states_error_summary', 'get_states_extra_msg')
    return result


def setup_transitions(permissions, states):
    transitions = workflow_constants.DEFAULT_TRANSITIONS
    for plugin in common.PluginImplementations(IWorkflow):
        transitions = plugin.get_transitions(transitions)

    # check if all id's are unique
    transition_ids = [(t.get("from_state", None), t.get("to_state", None)) for t in transitions]
    if len(transition_ids) > len(set(transition_ids)):
        raise common.ValidationError("transition_ids")

    # validate all transitions
    transition_schema = workflow_transition_schema(permissions, states)
    errors = {}
    result = []
    for transition in transitions:
        transition_dict, transition_errors = common.navl_validate(transition, transition_schema, {})
        if not transition_errors:
            result.append(transition_dict)
        else:
            errors[(transition_dict.get("from_state", None), transition_dict.get("to_state", None))] = transition_errors
    if errors:
        raise common.ValidationError(errors, 'get_transitions_error_summary', 'get_transitions_extra_msg')
    return result


def setup_update_actions():
    def default_getter(*fields):
        def getter(context, data_dict):
            if data_dict is None or context.get('ignore_workflow', False):
                return []
            return [data_dict.get(field, None) for field in fields]
        return getter

    update_actions = {
        'package_update': default_getter('id'),
        'package_relationship_create': default_getter('subject', 'object'),
        'package_relationship_update': default_getter('subject', 'object'),
        'package_relationship_delete': default_getter('subject', 'object')
    }

    for plugin in common.PluginImplementations(IWorkflow):
        update_actions = plugin.get_update_actions(update_actions)

    # validate all transitions
    schema = workflow_update_action_schema()
    errors = {}
    for update_action in update_actions:
        action_getter = update_actions.get(update_action)
        if action_getter is None:
            action_getter = default_getter
            update_actions[update_action] = action_getter
        data = {'action': update_action, 'getter': update_actions.get(update_action)}
        _, update_action_errors = common.navl_validate(data, schema, {})
        if update_action_errors:
            errors[update_action] = update_action_errors

    if errors:
        raise common.ValidationError(errors, 'get_update_actions_error_summary', 'get_update_actions_extra_msg')

    return update_actions


class WorkflowBackend(object):

    transition_dict = {}
    states_dict = {}
    update_actions_dict = {}
    default_state = None

    @classmethod
    def setup(cls):

        permissions = AuthorizationBackend.get_permissions()
        cls.update_actions_dict = setup_update_actions()
        states = setup_states(cls.update_actions_dict.keys(), permissions)
        cls.states_dict = {state['id']: WorkflowState(**state) for state in states}
        cls.default_state = setup_default_state(cls.get_states())
        for t in setup_transitions(permissions, cls.get_states()):
            cls.transition_dict.setdefault(t["from_state"], {}).setdefault(t["to_state"], WorkflowTransition(**t))

    @classmethod
    def has_transition(cls, from_state_id, to_state_id):
        return from_state_id in cls.transition_dict and to_state_id in cls.transition_dict[from_state_id]

    @classmethod
    def get_transition(cls, from_state_id, to_state_id):
        result = None
        if cls.has_transition(from_state_id, to_state_id):
            result = cls.transition_dict[from_state_id][to_state_id]
        return result

    @classmethod
    def get_transitions(cls):
        return [(key, subkey) for key in cls.transition_dict for subkey in cls.transition_dict[key]]

    @classmethod
    def has_state(cls, state_id):
        return state_id in cls.states_dict

    @classmethod
    def has_state_transitions(cls, state_id):
        return bool(cls.transition_dict.get(state_id, {}))

    @classmethod
    def get_state(cls, state_id) -> WorkflowState:
        result = None
        if cls.has_state(state_id):
            result = cls.states_dict[state_id]
        # elif cls.default_state:
        #     result = cls.states_dict[cls.default_state]
        return result

    @classmethod
    def get_states(cls) -> List[str]:
        return list(cls.states_dict.keys())

    @classmethod
    def allowed_states(cls, context, state_id, user_id, pkg_id, org_id, actions=None):
        """

        :param Dict context:
        :param str state_id:
        :param str user_id:
        :param str pkg_id:
        :param str org_id:
        :param Optional[List[str]] actions:
        :return:
        """
        if actions is None:
            return []
        elif not isinstance(actions, list):
            actions = [actions]

        sysadmin = is_sysadmin(user_id)
        if sysadmin:
            return [state for state in cls.get_states() if state != state_id]

        states = []

        if state_id in cls.transition_dict:
            for t_id in cls.transition_dict[state_id]:
                t = cls.transition_dict[state_id][t_id]
                # check if we are allowed from state to transition.state
                # if self.can_request()
                request_allowed = t.request_allowed(context, user_id, pkg_id, org_id)
                approve_allowed = t.approve_allowed(context, user_id, pkg_id, org_id)
                assign_allowed = t.assign_allowed(context, user_id, pkg_id, org_id)

                d = {
                    "request": request_allowed,
                    "approve": approve_allowed,
                    "assign": assign_allowed,
                }

                if any([d.get(k) for k in d if k in actions]):
                    states.append(t.to_state)

        return states
