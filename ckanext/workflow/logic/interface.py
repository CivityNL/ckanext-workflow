from ckan.plugins.interfaces import Interface
from ckan.plugins import toolkit
from typing import List, Union, Optional
from ckanext.workflow.logic.validators import is_function_with_parameters as _is_function_with_parameters_validator
import ckanext.workflow.constants as workflow_constants
from ckan.authz import users_role_for_group_or_org, has_user_permission_for_group_or_org, user_is_collaborator_on_dataset


def is_function(value):
    result = True
    try:
        _is_function_with_parameters_validator(["context", "pkg_dict"])(value)
    except toolkit.Invalid:
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
        print("_WorkflowObject __init__")
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
        print("WorkflowState __init__")
        self.id = None
        self.dataset_fields = None
        self.can_update = None
        self.on_update = None
        self.update_events = None        
        self.transitions: List[WorkflowTransition] = []
        super().__init__(**kwargs)

    def add_transition(self, transition):
        self.transitions.append(transition)

    def has_transitions(self):
        return len(self.transitions) > 0



class WorkflowTransition(_WorkflowObject):

    def __init__(self, **kwargs):
        print(f"WorkflowTransition __init__ kwargs = {kwargs}")
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
        result = False
        for check in checks:
            if is_function(check):
                result = check(context=None, pkg_dict=None)
            elif check in workflow_constants.CAPACITIES:
                result = users_role_for_group_or_org(org_id, user_id) == check
                if not result:
                    result = user_is_collaborator_on_dataset(user_id, pkg_id, check)
            elif check in workflow_constants.PERMISSIONS:
                result = has_user_permission_for_group_or_org(org_id, user_id, check.split(workflow_constants.PERMISSION_PREFIX, 1)[1])
            if result:
                break
        return result

    def request_allowed(self, context, user_id, pkg_id, org_id):
        return self._check_allowed(context, self.can_request, user_id, pkg_id, org_id)

    def approve_allowed(self, context, user_id, pkg_id, org_id):
        return self._check_allowed(context, self.can_approve, user_id, pkg_id, org_id)

    def set_origin(self, origin):
        self.origin = origin

    def set_destination(self, destination):
        self.destination = destination        

    @property    
    def id(self):
        return "{}-{}".format(self.origin.id, self.destination.id)
    


class Workflow(object):

    def get_state(self, state_id) -> WorkflowState:
        return next((state for state in self.states if state.id == state_id), None)

    def get_states(self):
        return [state.id for state in self.states]

    def __init__(self, states):
        print("Workflow __init__")
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
        self.default_state = default_state

    def set_states(self, states):
        self.states = states
        if self.transitions:
            self._init_states()

    def set_transitions(self, transitions):
        self.transitions = transitions
        if self.states:
            self._init_states()

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


class IWorkflow(Interface):

    def get_default_state(self):
        pass


    def get_states(self, states):
        return states

    def get_transitions(self, transitions):
        return transitions

    def get_roles(self, roles):
        return roles
