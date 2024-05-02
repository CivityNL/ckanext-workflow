from typing import Dict, Callable

from ckan.lib.navl.dictization_functions import unflatten
from ckanext.workflow.model import WorkflowRequest
from ckan.plugins import toolkit
import ckanext.workflow.helpers as workflow_helpers
import ckanext.workflow.constants as workflow_constants

# noinspection PyProtectedMember
_ = toolkit._

unicode_only = toolkit.get_validator("unicode_only")
one_of = toolkit.get_validator("one_of")


def request_id_does_not_exist(request_id: str) -> str:
    """
        Returns:
            the given value if a WorkflowRequest identified by the request_id can be found
        Raises:
            Invalid if not found
    """
    result = WorkflowRequest.get(request_id)
    if result:
        raise toolkit.Invalid(_('Request id already exists'))
    return request_id


def organization_id_exists(organization_id: str, context: Dict) -> str:
    """
        Raises Invalid if an organization identified by the id cannot be found
    """
    model = context['model']
    session = context['session']

    result = session.query(model.Group).get(organization_id)
    if not result or not result.is_organization:
        raise toolkit.Invalid('%s: %s' % (_('Not found'), _('Organization')))
    return organization_id


def state_exists(state):
    if state not in workflow_constants.WORKFLOW.get_states():
        raise toolkit.Invalid('%s: %s' % (_('Not found'), _('WorkflowState')))
    return state


def request_approval_validator(key, converted_data, errors, context):
    pass


def is_function(value: Callable):
    """
        Raises Invalid if the given value is not a function (can't be called)
    """
    if not callable(value) and not hasattr(value, "__call__"):
        raise toolkit.Invalid(_('Value must be a function'))
    return value


def is_function_with_parameters(varnames):
    """
        Returns a 
    """

    '''Raises Invalid if the given value is not a function (can't be called)'''

    def f(value: Callable):
        value = is_function(value)
        # noinspection PyUnresolvedReferences
        func_varnames = set(value.__code__.co_varnames[:value.__code__.co_argcount])
        if not func_varnames == set(varnames):
            raise toolkit.Invalid(_('is_function_with_parameters'))
        return value

    return f


def is_text_function(text_function: Callable[[], str]) -> Callable[[], str]:
    """_summary_

    Args:
        text_function (Callable[[], str]): _description_

    Returns:
        Callable[[], str]: _description_
    """
    unicode_only(is_function(text_function)())
    return text_function


def list_one_of(list_of_value):
    def _list_one_of(value):
        if not isinstance(value, list):
            value = [value]
        for v in value:
            one_of(list_of_value)(v)
        return value

    return _list_one_of


def one_of_validators(list_of_validators):
    def _one_of_validators(value):
        for validator in list_of_validators:
            try:
                validator(value)
                return value
            except toolkit.Invalid as e:
                pass
        raise toolkit.Invalid(_('Value must be one of {}'.format(list_of_validators)))

    return _one_of_validators


def list_one_of_validators(list_of_validators):
    def _list_one_of_validators(value):
        if not isinstance(value, list):
            value = [value]
        for v in value:
            one_of_validators(list_of_validators)(v)
        return value

    return _list_one_of_validators


def workflow_state_after_validator(key, converted_data, errors, context):
    """

    :param key:
    :param converted_data:
    :param errors:
    :param context:
    :return:
    """

    def add_error(key, error):
        """

        :param key:
        :param error:
        """
        errors[(key,)].append(error)

    if any(errors[key] for key in errors):
        # something is already wrong, so no need to do this check
        return

    pkg = context.get("package", None)

    if pkg is None:
        # let's assume we started with the default
        before_state = workflow_constants.DEFAULT_STATE.id
    else:
        before_state = workflow_helpers._get_state_pkg(pkg).id

    # let's see if we can deal with the rest now
    user_id = context['auth_user_obj'].id
    pkg_id = converted_data.get(("id",))
    pkg_type = converted_data.get(("type",))
    owner_org = converted_data.get(("owner_org",))
    after_state = converted_data.get((workflow_constants.DEFAULT_FIELD,))

    # we'll need to revalidate the state field as this is also based on the organization
    if owner_org and workflow_helpers.workflow_enabled_for_organization(owner_org):
        if not after_state:
            # workflow state field required
            add_error(workflow_constants.DEFAULT_FIELD, toolkit._('Missing value'))
        else:
            if before_state != after_state:
                allowed_states = workflow_constants.WORKFLOW.allowed_states(
                    context, before_state, user_id, pkg_id, owner_org, actions="assign"
                )
                if after_state not in allowed_states:
                    add_error(
                        workflow_constants.DEFAULT_FIELD,
                        toolkit._('Value must be one of {}'.format(allowed_states))
                    )

            state = workflow_constants.WORKFLOW.get_state(after_state)
            if state.dataset_fields:
                for field in state.dataset_fields:
                    field_value = state.dataset_fields.get(field)
                    if converted_data.get((field,)) != field_value:
                        add_error(
                            field,
                            toolkit._(
                                'The state {state} requires this field to have the value of {value}'.format(
                                    state=after_state, value=field_value
                                )
                            )
                        )
    else:
        if after_state:
            add_error(workflow_constants.DEFAULT_FIELD, toolkit._('Value must be one of {}'.format([None])))

    # if there are no errors
    if not any(errors[key] for key in errors):
        # convert the converted_data into a bit easier to use and remove the extras as they are duplicated
        data_dict = dict(unflatten(converted_data))
        del data_dict['extras']

        # convert the pkg into a dict and add the extras to make it easier to compare
        pkg_dict = dict(pkg.as_dict())
        pkg_dict.update(pkg_dict.pop('extras', {}))

        changed_fields = set()
        set_keys = set(pkg_dict.keys()).union(set(data_dict.keys()))
        for key in set_keys:
            if key in pkg_dict and key not in data_dict:
                pass
            elif key not in pkg_dict and key in data_dict:
                changed_fields.add(key)
            else:
                if not pkg_dict.get(key) == data_dict.get(key):
                    changed_fields.add(key)
        if workflow_constants.DEFAULT_FIELD in changed_fields:
            state = workflow_constants.WORKFLOW.get_state(after_state)
            state_fields = set([workflow_constants.DEFAULT_FIELD])
            if state.dataset_fields:
                state_fields.update(set(state.dataset_fields.keys()))
            if not changed_fields - state_fields:
                converted_data[('is_workflow_set_state',)] = True

