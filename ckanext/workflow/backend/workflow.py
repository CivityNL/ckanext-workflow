from ckanext.workflow.backend.schema import workflow_state_schema, workflow_transition_schema, \
    workflow_update_action_schema
import ckanext.workflow.common as common
from ckanext.workflow.backend.validators import is_function_with_parameters

# logging
import logging

from ckanext.workflow.interface import IWorkflow
from ckanext.workflow.common import Invalid, is_sysadmin, has_user_permission_for_package, h, config


log = logging.getLogger(__name__)


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



def is_function(value):
    result = True
    try:
        is_function_with_parameters(["context", "pkg_dict"])(value)
    except Invalid:
        result = False
    return result


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
            raise common.ValidationError(default_state, 'get_default_state_error_summary', 'get_default_state_extra_msg')
        cls.default_state = default_state[0]

        transitions = specification.get('transitions', [])
        cls.set_transitions(transitions)

    @classmethod
    def set_states(cls, states):
        # validate all states
        state_ids = [state.get('id') for state in states]
        state_schema = workflow_state_schema(cls.get_update_actions(), list(common.get_permissions().keys()), state_ids)

        errors = {}
        for state in states:
            state_dict, state_errors = common.navl_validate(state, state_schema, {})
            print(f"state_dict={state_dict}, state_errors={state_errors}")
            cls.states_dict[state['id']] = state_dict
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
        transition_schema = workflow_transition_schema(list(common.get_permissions().keys()), cls.get_states())
        errors = {}
        for transition in transitions:
            transition_dict, transition_errors = common.navl_validate(transition, transition_schema, {})
            cls.transition_dict \
                .setdefault(transition_dict["from_state"], {}) \
                .setdefault(transition_dict["to_state"], transition_dict)
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
    def get_state(cls, state_id):
        '''
        Get a list of all the defined states in the WorkflowBackend

        :param state_id: identifier of the state to retrieve
        :type state_id: string

        :return: state with the given ``state_id``
        :rtype: list of strings

        :raises ObjectNotFound: if there is no state matching the given ``state_id``
        '''
        return cls.states_dict[cls.get_state_id(state_id)]

    @classmethod
    def get_state_id(cls, state_id):
        result = None
        if cls.has_state(state_id):
            result = state_id
        elif state_id is None and cls.default_state:
            result = cls.default_state
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
    def allowed_transitions(cls, context, state_id, user_id, pkg_id, org_id, actions=None):
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
            actions = ["request", "approve", "assign"]
        elif not isinstance(actions, list):
            actions = [actions]

        transitions = {}

        if state_id in cls.transition_dict:
            for t_id in cls.transition_dict[state_id]:
                # check if we are allowed from state to transition.state

                d = {
                    "request": cls.request_allowed(context, state_id, t_id, user_id, pkg_id, org_id),
                    "approve": cls.approve_allowed(context, state_id, t_id, user_id, pkg_id, org_id),
                    "assign": cls.assign_allowed(context, state_id, t_id, user_id, pkg_id, org_id),
                }

                if any([d.get(k) for k in d if k in actions]):
                    transitions[(state_id, t_id)] = [k for k,v in d.items() if v]

        return transitions

    @classmethod
    def get_update_actions(cls):
        if not cls.update_actions_dict:
            raise NotImplemented
        return list(cls.update_actions_dict.keys())

    @classmethod
    def get_update_actions_for_state(cls, state_id):
        print(f"get_update_actions_for_state(state_id='{state_id}')")
        if not cls.has_state(state_id):
            return []
        else:
            return cls.get_state(state_id).get('update_actions', [])

    @classmethod
    def get_dataset_fields_for_state(cls, state_id):
        print(f"get_dataset_fields_for_state(state_id='{state_id}')")
        if not cls.has_state(state_id):
            return []
        else:
            return cls.get_state(state_id).get('dataset_fields', {})


    @classmethod
    def is_update_action_allowed_for_state(cls, state_id, update_action, user_id, pkg_id):
        print(f"is_update_action_allowed_for_state(state_id='{state_id}', update_action='{update_action}', user_id='{user_id}', pkg_id='{pkg_id}')")
        if not cls.has_state(state_id):
            return False
        update_actions = {
            ua.get('permission'): ua.get('to_state', None) 
            for ua in cls.get_update_actions_for_state(state_id) 
            if ua.get('action') == update_action
        }
        result = False
        for permission in update_actions:
            if has_user_permission_for_package(pkg_id, user_id, permission):
                result = True
                break
        return result


    @classmethod
    def validate_package_for_state(cls, state_id, pkg_dict):
        print(f"validate_package_for_state(state_id='{state_id}', pkg_dict='{pkg_dict}')")
        dataset_fields = cls.get_dataset_fields_for_state(state_id)
        pkg_fields = {f: pkg_dict.get(f) for f in pkg_dict if f != 'extras'}
        pkg_extra_fields = {extra.get('key'): extra.get('value') for extra in pkg_dict.get('extras', [])}
        errors = {}
        if dataset_fields:
            for field in dataset_fields:
                field_value = dataset_fields[field]
                if field in pkg_fields:
                    value = pkg_fields.get(field)
                elif field in pkg_extra_fields:
                    value = pkg_extra_fields.get(field)
                else:
                    errors[field] = ['Missing']
                    continue
                if field_value != value:
                    errors[field] = ['Expected {field_value} but got {value}'.format(
                        field_value=field_value, value=value
                    )]
        return errors


    @classmethod
    def get_state_after_update_action(cls, state_id, update_action, user_id, pkg_id):
        print(f"get_state_after_update_action(state_id='{state_id}', update_action='{update_action}', user_id='{user_id}', pkg_id='{pkg_id}')")

        update_actions = {
            ua.get('permission'): ua.get('to_state', None) 
            for ua in cls.get_update_actions_for_state(state_id) 
            if ua.get('action') == update_action
        }

        result = None
        for permission in update_actions:
            if has_user_permission_for_package(pkg_id, user_id, permission):
                result = update_actions[permission]
                break
        if result is None:
            result = state_id
        print(f"state_after_update_action -> {result}")
        return result
    
    @classmethod
    def _check_allowed(self, context, checks, user_id, pkg_id, org_id):
        # print(f"WorkflowTransition._check_allowed for checks={checks}, user_id={user_id}, pkg_id={pkg_id}, org_id={org_id}")
        result = is_sysadmin(user_id)
        for check in checks:
            if result:
                break
            # if is_function(check):
            #     result = check(context=context, pkg_dict=None)
            else:
                result = has_user_permission_for_package(pkg_id, user_id, check)
        return result

    @classmethod
    def request_allowed(cls, context, from_state, to_state, user_id, pkg_id, org_id):
        if not cls.has_transition(from_state, to_state):
            return False
        checks = cls.get_transition(from_state, to_state).get('can_request', [])
        return cls._check_allowed(context, checks, user_id, pkg_id, org_id)

    @classmethod
    def approve_allowed(cls, context, from_state, to_state, user_id, pkg_id, org_id):
        if not cls.has_transition(from_state, to_state):
            return False
        checks = cls.get_transition(from_state, to_state).get('can_approve', [])
        return cls._check_allowed(context, checks, user_id, pkg_id, org_id)

    @classmethod
    def assign_allowed(cls, context, from_state, to_state, user_id, pkg_id, org_id):
        if not cls.has_transition(from_state, to_state):
            return False
        checks = cls.get_transition(from_state, to_state).get('can_assign', [])
        return cls._check_allowed(context, checks, user_id, pkg_id, org_id)

    @classmethod
    def get_transition_label(cls, from_state, to_state):
        return language_text(cls.get_transition(from_state, to_state).get('label', {}))

    @classmethod
    def get_state_label(cls, state_id):
        return language_text(cls.get_state(state_id).get('label', {}))
    