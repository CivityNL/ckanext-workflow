from ckanext.workflow.backend.classes import WorkflowState, WorkflowTransition
from ckanext.workflow.backend.schema import workflow_state_schema, workflow_transition_schema, \
    workflow_update_action_schema
import ckanext.workflow.common as common

# logging
import logging

from ckanext.workflow.interface import IWorkflow

log = logging.getLogger(__name__)


def default_getter(*fields):
    def getter(context, data_dict):
        pkg_ids = []
        if data_dict is None or context.get('ignore_workflow', False):
            return pkg_ids
        for field in fields:
            if isinstance(field, list):
                pkg_id = next((data_dict.get(f) for f in field if data_dict.get(f, None) is not None), None)
            else:
                pkg_id = data_dict.get(field, None)
            pkg_ids.append(pkg_id)
        return pkg_ids

    return getter


class WorkflowBackend(object):
    transition_dict = {}
    states_dict = {}
    update_actions_dict = {}
    default_state = None

    @classmethod
    def setup(cls, specification):

        cls.update_actions_dict = cls.set_update_actions()

        # let's parse the crap out of this specification
        specification_states = [dict(state, id=key) for key, state in specification.get('states', {}).items()]
        cls.set_states(specification_states)

        default_state = [state.get('id') for state in specification_states if state.get('default', False)]
        if len(default_state) != 1:
            raise common.ValidationError(default_state, 'get_states_error_summary', 'get_states_extra_msg')
        cls.default_state = default_state[0]

        transitions = specification.get('transitions', [])
        cls.set_transitions(transitions)

    @classmethod
    def set_states(cls, states):
        # validate all states
        state_ids = [state.get('id') for state in states]
        state_schema = workflow_state_schema(cls.get_update_actions(), common.get_permissions(), state_ids)

        errors = {}
        for state in states:
            state_dict, state_errors = common.navl_validate(state, state_schema, {})
            cls.states_dict[state['id']] = WorkflowState(**state_dict)
            if state_errors:
                errors[state_dict.get("id", None)] = state_errors
        if errors:
            raise common.ValidationError(errors, 'get_states_error_summary', 'get_states_extra_msg')

    @classmethod
    def set_transitions(cls, transitions):
        # check if all id's are unique
        transition_ids = [
            (transition.get("from_state", None), transition.get("to_state", None)) for transition in transitions
        ]
        if len(transition_ids) > len(set(transition_ids)):
            raise common.ValidationError("transition_ids")

        # validate all transitions
        transition_schema = workflow_transition_schema(common.get_permissions(), cls.get_states())
        errors = {}
        for transition in transitions:
            transition_dict, transition_errors = common.navl_validate(transition, transition_schema, {})
            cls.transition_dict \
                .setdefault(transition_dict["from_state"], {}) \
                .setdefault(transition_dict["to_state"], WorkflowTransition(**transition_dict))
            if transition_errors:
                errors[(transition_dict.get("from_state", None),
                        transition_dict.get("to_state", None))] = transition_errors
        if errors:
            raise common.ValidationError(errors, 'get_transitions_error_summary', 'get_transitions_extra_msg')

    @classmethod
    def set_update_actions(cls):
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
                update_actions[update_action] = default_getter(['package_id', 'id', 'name'])
            _, update_action_errors = common.navl_validate(
                {'action': update_action, 'getter': update_actions.get(update_action)},
                schema,
                {}
            )
            if update_action_errors:
                errors[update_action] = update_action_errors

        if errors:
            raise common.ValidationError(errors, 'get_update_actions_error_summary', 'get_update_actions_extra_msg')

        return update_actions

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
        if not cls.transition_dict:
            raise NotImplemented
        return [(key, subkey) for key in cls.transition_dict for subkey in cls.transition_dict[key]]

    @classmethod
    def has_state(cls, state_id):
        """
        """
        return state_id in cls.states_dict

    @classmethod
    def has_state_transitions(cls, state_id):
        '''
        Check if a given state has any transitions

        :param state_id: identifier of the state to retrieve
        :type state_id: string

        :return: `True` if any transitions could be found, otherwise `False`
        :rtype: boolean
        '''
        return bool(cls.transition_dict.get(state_id, {}))

    @classmethod
    def get_state(cls, state_id) -> WorkflowState:
        '''
        Get a list of all the defined states in the WorkflowBackend

        :param state_id: identifier of the state to retrieve
        :type state_id: string

        :return: state with the given ``state_id``
        :rtype: list of strings

        :raises ObjectNotFound: if there is no state matching the given ``state_id``
        '''
        result = None
        if cls.has_state(state_id):
            result = cls.states_dict[state_id]
        # elif cls.default_state:
        #     result = cls.states_dict[cls.default_state]
        else:
            raise common.ObjectNotFound("Could not find any states with '{}'".format(state_id))
        return result

    @classmethod
    def get_states(cls):
        '''
        Get a list of all the defined states in the WorkflowBackend

        :return: list of identifiers for all states
        :rtype: list of strings
        '''
        if not cls.states_dict:
            raise NotImplemented
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

        sysadmin = common.is_sysadmin(user_id)
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

    @classmethod
    def get_update_actions(cls):
        if not cls.update_actions_dict:
            raise NotImplemented
        return list(cls.update_actions_dict.keys())
