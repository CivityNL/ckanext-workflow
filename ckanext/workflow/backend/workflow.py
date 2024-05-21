from typing import Callable, Dict, List

from ckanext.workflow.backend.validators import is_function_with_parameters
import ckanext.workflow.constants as workflow_constants
from ckan.authz import users_role_for_group_or_org, has_user_permission_for_group_or_org, \
    user_is_collaborator_on_dataset, is_sysadmin
import ckanext.workflow.common as common

# logging
import logging

log = logging.getLogger(__name__)



def is_function(value):
    result = True
    try:
        is_function_with_parameters(["context", "pkg_dict"])(value)
    except common.Invalid:
        result = False
    return result


class _WorkflowObject(object):

    @property
    def label(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self._label()

    def validate(self, schema, **kwargs):
        data, errors = common.navl_validate(kwargs, schema)
        if errors:
            raise common.ValidationError(errors)
        return data

    def __init__(self, schema, **kwargs):
        data = self.validate(schema, **kwargs)
        data["_label"] = data.pop("label", None)
        self.__dict__.update(data)

    def __repr__(self):
        attribute_repr = []
        for k in self.__dict__:
            v = self.__dict__.get(k)
            if isinstance(v, list):
                attribute_repr.append("{}[{}]:{}".format(k, len(v), v))
            else:
                attribute_repr.append("{}:{}".format(k, v))
        return f"<{self.__class__.__name__} {' '.join(attribute_repr)}>"







class WorkflowState(_WorkflowObject):

    def __init__(self, **kwargs):
        self.id = None
        self.dataset_fields = None
        self.can_update = None
        self.on_update = None
        self.update_actions: List[Dict[str, Callable]] = []
        self.transitions: List[WorkflowTransition] = []
        super().__init__(**kwargs)

    def add_transition(self, transition):
        self.transitions.append(transition)

    def has_transitions(self):
        return len(self.transitions) > 0

    def state_on_update(self, action, context, pkg_dict):
        print(f"state_on_update -> {self.on_update}")
        if self.on_update is None:
            result = self.id
        elif not isinstance(self.on_update, dict):
            result = self.on_update
        elif not action in self.on_update:
            result = self.id
        else:
            on_update_action = self.on_update[action]
            if is_function(on_update_action):
                result = on_update_action(context=context, pkg_dict=pkg_dict)
            else:
                result = on_update_action
        print(f"state_on_update -> {result}")
        return result

    def update_allowed(self, context, user_id, pkg_id, org_id):
        return self._check_allowed(context, self.can_update, user_id, pkg_id, org_id)

    def _check_allowed(self, context, checks, user_id, pkg_id, org_id):
        result = is_sysadmin(user_id)
        for check in checks:
            if result:
                break
            if is_function(check):
                result = check(context=context, pkg_dict=None)
            elif check in workflow_constants.CAPACITIES:
                result = users_role_for_group_or_org(org_id, user_id) == check
                if not result:
                    result = user_is_collaborator_on_dataset(user_id, pkg_id, check)
            elif check in workflow_constants.PERMISSIONS:
                result = has_user_permission_for_group_or_org(org_id, user_id,
                                                              check.split(workflow_constants.PERMISSION_PREFIX, 1)[1])
        return result


class WorkflowTransition(_WorkflowObject):

    def __init__(self, **kwargs):
        self.origin = None
        self.destination = None
        self.request_required = None
        self.can_request = []
        self.can_approve = []
        self.request_message_required = None
        self.approve_message_required = None
        self.reject_message_required = None
        super().__init__(**kwargs)

    def _check_allowed(self, context, checks, user_id, pkg_id, org_id):
        result = is_sysadmin(user_id)
        for check in checks:
            if result:
                break
            if is_function(check):
                result = check(context=context, pkg_dict=None)
            elif check in workflow_constants.CAPACITIES:
                result = users_role_for_group_or_org(org_id, user_id) == check
                if not result:
                    result = user_is_collaborator_on_dataset(user_id, pkg_id, check)
            elif check in workflow_constants.PERMISSIONS:
                result = has_user_permission_for_group_or_org(org_id, user_id,
                                                              check.split(workflow_constants.PERMISSION_PREFIX, 1)[1])
        return result

    def request_allowed(self, context, user_id, pkg_id, org_id):
        return self._check_allowed(context, self.can_request, user_id, pkg_id, org_id)

    def approve_allowed(self, context, user_id, pkg_id, org_id):
        return self._check_allowed(context, self.can_approve, user_id, pkg_id, org_id)

    def set_origin(self, origin: WorkflowState):
        self.origin = origin

    def set_destination(self, destination: WorkflowState):
        self.destination = destination

    @property
    def id(self):
        return "{}-{}".format(self.origin.id, self.destination.id)


class WorkflowBackend(object):
    class _WorkflowTransition:
        pass

    class _WorkflowState:
        pass

    @classmethod
    def __repr__(cls):
        attribute_repr = []
        for k in cls.__dict__:
            v = cls.__dict__.get(k)
            if isinstance(v, list):
                attribute_repr.append("{}[{}]:{}".format(k, len(v), v))
            else:
                attribute_repr.append("{}:{}".format(k, v))
        return f"<{cls.__class__.__name__} {' '.join(attribute_repr)}>"

    transition_dict = {}
    states_dict = {}
    update_actions_dict = {}

    @classmethod
    def setup(cls):

        roles = common.h.authorization_get_permissions()
        print(roles)

    def has_transition(self, from_state_id, to_state_id):
        return from_state_id in self.transition_dict and to_state_id in self.transition_dict[from_state_id]

    def get_transition(self, from_state_id, to_state_id):
        result = None
        if self.has_transition(from_state_id, to_state_id):
            result = self.transition_dict[from_state_id][to_state_id]
        return result

    def get_transitions(self):
        return [(key, subkey) for key in self.transition_dict for subkey in self.transition_dict[key]]

    def has_state(self, state_id):
        return state_id in self.states_dict

    def get_state(self, state_id) -> WorkflowState:
        result = None
        if self.has_state(state_id):
            result = self.states_dict[state_id]
        return result

    def get_states(self):
        return list(self.states_dict.keys())

    def __init__(self, states, transitions, update_actions=None, default_state=None):
        self.states_dict = {state.id: state for state in states}
        # init
        for transition in transitions:
            if transition.from_state not in self.transition_dict:
                self.transition_dict[transition.from_state] = {}
            self.transition_dict[transition.from_state][transition.to_state] = transition

        self.update_actions_dict = update_actions
        self.default_state = default_state

    def allowed_states(self, context, state_id, user_id, pkg_id, org_id, actions=None, origin=None, states=None):
        if actions is None:
            return []
        elif not isinstance(actions, list):
            actions = [actions]

        sysadmin = is_sysadmin(user_id)
        if sysadmin:
            return [state for state in self.get_states() if state != state_id]

        if states is None:
            states = []
        if origin is None:
            origin = state_id

        state = self.get_state(state_id)
        if state.has_transitions():
            for transition in state.transitions:
                if transition.destination.id not in states + [origin]:
                    # check if we are allowed from state to transition.state
                    # if self.can_request()
                    request_allowed = transition.request_allowed(context, user_id, pkg_id, org_id)
                    approve_allowed = transition.approve_allowed(context, user_id, pkg_id, org_id)
                    assign_allowed = (request_allowed or not transition.request_required) and approve_allowed

                    d = {
                        "request": request_allowed,
                        "approve": approve_allowed,
                        "assign": assign_allowed,
                    }

                    if any([d.get(k) for k in d if k in actions]):
                        states.append(transition.destination.id)

                    if assign_allowed:
                        states = self.allowed_states(context, transition.destination.id, user_id, pkg_id, org_id,
                                                     actions, origin, states)

        return states
