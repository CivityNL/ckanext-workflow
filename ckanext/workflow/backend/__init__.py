from ckan.plugins.interfaces import Interface
from ckan.plugins import toolkit
from typing import Callable, Dict, List
from ckanext.workflow.logic.validators import is_function_with_parameters as _is_function_with_parameters_validator
import ckanext.workflow.constants as workflow_constants
from ckan.authz import users_role_for_group_or_org, has_user_permission_for_group_or_org, user_is_collaborator_on_dataset

_Invalid = toolkit.Invalid # type: ignore
_check_access = toolkit.check_access # type: ignore

def is_function(value):
    result = True
    try:
        _is_function_with_parameters_validator(["context", "pkg_dict"])(value)
    except _Invalid:
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
        
    def __init__(self, **kwargs):
        self._label: Callable
        if "label" in kwargs:
            kwargs["_label"] = kwargs.pop("label")
        self.__dict__.update(kwargs)


    def __repr__(self):
        attribute_repr = []
        for k in self.__dict__:
            v = self.__dict__.get(k)
            if isinstance(v, list):
                attribute_repr.append("n_{}:{}".format(k, len(v)))
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
        result = self.id
        if self.on_update is not None:
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
        return result


    def update_allowed(self, context, user_id, pkg_id, org_id):
        return self._check_allowed(context, self.can_update, user_id, pkg_id, org_id)    

    def _check_allowed(self, context, checks, user_id, pkg_id, org_id):
        result = _check_access('sysadmin', context, {})
        for check in checks:
            if result:
                break            
            if is_function(check):
                result = check(context=None, pkg_dict=None)
            elif check in workflow_constants.CAPACITIES:
                result = users_role_for_group_or_org(org_id, user_id) == check
                if not result:
                    result = user_is_collaborator_on_dataset(user_id, pkg_id, check)
            elif check in workflow_constants.PERMISSIONS:
                result = has_user_permission_for_group_or_org(org_id, user_id, check.split(workflow_constants.PERMISSION_PREFIX, 1)[1])
        return result    



class WorkflowTransition(_WorkflowObject):

    def __init__(self, **kwargs):
        self.origin: WorkflowState
        self.destination: WorkflowState
        self.request_required = None
        self.can_request = []
        self.can_approve = []
        self.request_message_required = None        
        self.approve_message_required = None
        self.reject_message_required = None
        super().__init__(**kwargs)

    def _check_allowed(self, context, checks, user_id, pkg_id, org_id):
        result = _check_access('sysadmin', context, {})
        for check in checks:
            if result:
                break            
            if is_function(check):
                result = check(context=None, pkg_dict=None)
            elif check in workflow_constants.CAPACITIES:
                result = users_role_for_group_or_org(org_id, user_id) == check
                if not result:
                    result = user_is_collaborator_on_dataset(user_id, pkg_id, check)
            elif check in workflow_constants.PERMISSIONS:
                result = has_user_permission_for_group_or_org(org_id, user_id, check.split(workflow_constants.PERMISSION_PREFIX, 1)[1])
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
    


class Workflow(object):


    def get_state(self, state_id) -> WorkflowState:
        state = None
        if state_id in self.get_states():
            state = next(state for state in self.states if state.id == state_id)
        return state

    def get_states(self):
        return [state.id for state in self.states]

    def __init__(self, states):
        self.transitions = []
        self.default_state = None
        self.set_states(states)

    def _init_states(self):
        for transition in self.transitions:
            to_state = self.get_state(transition.to_state)
            transition.set_destination(to_state)
            from_state = self.get_state(transition.from_state)
            transition.set_origin(from_state)
            from_state.add_transition(transition)

    def set_default_state(self, default_state):
        self.default_state = self.get_state(default_state)

    def set_states(self, states: List[WorkflowState]):
        self.states = states
        if self.transitions:
            self._init_states()

    def set_transitions(self, transitions):
        self.transitions = transitions
        if self.states:
            self._init_states()

    def set_update_actions(self, update_actions):
        self.update_actions = update_actions

    def allowed_states(self, context, state_id, user_id, pkg_id, org_id, actions=None, origin=None, states=None):
        if actions is None:
            return []
        elif not isinstance(actions, list):
            actions = [actions]

        sysadmin = toolkit.check_access('sysadmin', context, {})
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
                        states = self.allowed_states(context, transition.destination.id, user_id, pkg_id, org_id, actions, origin, states)

        return states
