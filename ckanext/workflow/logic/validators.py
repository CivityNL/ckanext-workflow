from typing import Dict, Callable

from ckanext.workflow.backend import WorkflowBackend
from ckanext.workflow.model import WorkflowPackageRequest, WorkflowPackageState
from ckanext.workflow.model.workflow_package_request import REQUEST_STATE_PENDING, REQUEST_STATE_APPROVED, \
    REQUEST_STATE_REJECTED
import ckanext.workflow.common as common
import ckanext.workflow.helpers as workflow_helpers
import ckanext.workflow.constants as workflow_constants
# logging
import logging

log = logging.getLogger(__name__)

unicode_only = common.get_validator("unicode_only")
one_of = common.get_validator("one_of")
empty = common.get_validator("empty")


def has_errors(fields, errors):
    return sum(len(errors.get((field,))) for field in fields) > 0


def get_values(fields, data):
    return [data.get((field,)) for field in fields]


def process_message_required(
        package_id_field='package_id', request_state_field='request_state',
        process_state_field='process_state', process_message_field='process_message'
):
    def _process_message_required(key, data, errors, context):
        print(f"process_message_required")
        fields = [package_id_field, request_state_field, process_state_field, process_message_field]
        if has_errors(fields, errors):
            return
        package_id, request_state, process_state, process_message = get_values(fields, data)
        workflow_state = WorkflowPackageState.get(package_id)
        workflow_transition = WorkflowBackend.get_transition(workflow_state.state_id, request_state)

        if not process_message and process_state in WorkflowPackageRequest.states(handled=True):
            if process_state == REQUEST_STATE_APPROVED and workflow_transition.approve_message_required:
                errors[(process_message_field,)].append(
                    common.ugettext('Process state "{}" requires a process_message').format(process_state)
                )
            if process_state == REQUEST_STATE_REJECTED and workflow_transition.reject_message_required:
                errors[(process_message_field,)].append(
                    common.ugettext('Process state "{}" requires a process_message').format(process_state)
                )

    return _process_message_required


def process_user_id_required(
        process_state_field='process_state', process_user_id_field='process_user_id'
):
    def _process_user_id_required(key, data, errors, context):
        print(f"process_user_id_required")
        process_state = data.get((process_state_field,))
        process_user_id = data.get((process_user_id_field,))
        # check if the current process_state makes sense
        if has_error(process_state_field, errors):
            return
        if process_state not in WorkflowPackageRequest.states(open=True):
            if process_user_id is common.missing or not process_user_id:
                errors[(process_user_id_field,)].append(
                    common.ugettext('Process state "{}" requires a process_user_id').format(process_state))

    return _process_user_id_required


def transition_exists(
        package_id_field='package_id', request_state_field='request_state'
):
    def _transition_exists(key, data, errors, context):
        print(f"_transition_exists")
        package_id = data.get((package_id_field,))
        request_state = data.get((request_state_field,))
        if has_errors([package_id_field, request_state_field], errors):
            return
        workflow_state = WorkflowPackageState.get(package_id)
        workflow_transition = None
        if workflow_state:
            workflow_transition = WorkflowBackend.get_transition(workflow_state.state_id, request_state)

        if workflow_state and not workflow_transition:
            errors[(request_state_field,)].append(
                common.ugettext('No transition exists from state "{}" to state "{}"').format(request_state,
                                                                                             workflow_state.state_id))

    return _transition_exists


def has_error(field, errors):
    return len(errors.get((field,))) > 0


def transition_exists(
        package_id_field='package_id', request_state_field='request_state'
):
    def _transition_exists(key, data, errors, context):
        print(f"_transition_exists")
        package_id = data.get((package_id_field,))
        request_state = data.get((request_state_field,))
        if has_errors([package_id_field, request_state_field], errors):
            return
        workflow_state = WorkflowPackageState.get(package_id)
        workflow_transition = None
        if workflow_state:
            workflow_transition = WorkflowBackend.get_transition(workflow_state.state_id, request_state)

        if workflow_state and not workflow_transition:
            errors[(request_state_field,)].append(
                common.ugettext('No transition exists from state "{}" to state "{}"').format(request_state,
                                                                                             workflow_state.state_id))

    return _transition_exists


def request_message_required(
        package_id_field='package_id', request_state_field='request_state', request_message_field='request_message'
):
    def _request_message_required(key, data, errors, context):
        print(f"_request_message_required")
        package_id = data.get((package_id_field,))
        request_state = data.get((request_state_field,))
        request_message = data.get((request_message_field,))
        if has_errors([package_id_field, request_state_field], errors):
            return
        workflow_state = WorkflowPackageState.get(package_id)
        workflow_transition = None
        if workflow_state:
            workflow_transition = WorkflowBackend.get_transition(workflow_state.state_id, request_state)

        if workflow_transition and workflow_transition.request_message_required:
            if request_message is common.missing or not request_message:
                errors[(request_message_field,)].append(common.ugettext('_request_message_required'))

    return _request_message_required


def request_does(key, data, errors, context):
    session = context["session"]
    if has_errors(['package_id', 'request_state'], errors):
        return
    filter_kwargs = {
        'package_id': data.get(('package_id',)),
        'request_state': data.get(('request_state',)),
        'process_state': REQUEST_STATE_PENDING
    }
    query = session.query(WorkflowPackageRequest).filter_by(**filter_kwargs)
    if query.first() is not None:
        raise common.Invalid(common.ugettext('request_does :: Request id already exists'))


def default_current_user(key, data, errors, context):
    value = data.get(key)
    if value is common.missing:
        data[key] = context["user"]


def package_has_workflow_state(package_id: str) -> str:
    """
        Returns:
            the given value if a WorkflowPackageRequest identified by the request_id can be found
        Raises:
            Invalid if not found
    """
    result = WorkflowPackageState.get(package_id)
    if not result:
        raise common.Invalid(common.ugettext('Package does not have a WorkflowPackageState'))
    return package_id


def request_id_does_not_exist(request_id: str) -> str:
    """
        Returns:
            the given value if a WorkflowPackageRequest identified by the request_id can be found
        Raises:
            Invalid if not found
    """
    result = WorkflowPackageRequest.get(request_id)
    if result:
        raise common.Invalid(common.ugettext('Request id already exists'))
    return request_id


def request_id_exists(request_id: str) -> str:
    """
        Returns:
            the given value if a WorkflowPackageRequest identified by the request_id can be found
        Raises:
            Invalid if not found
    """
    result = WorkflowPackageRequest.get(request_id)
    if not result:
        raise common.Invalid(common.ugettext('Request id does not exist'))
    return request_id


def organization_id_exists(organization_id: str, context: Dict) -> str:
    """
        Raises Invalid if an organization identified by the id cannot be found
    """
    model = context['model']
    session = context['session']

    result = session.query(model.Group).get(organization_id)
    if not result or not result.is_organization:
        raise common.Invalid('%s: %s' % (common.ugettext('Not found'), common.ugettext('Organization')))
    return organization_id


def state_exists(state):
    """

    :param state:
    :return:
    """
    if state not in WorkflowBackend.get_states():
        raise common.Invalid('%s: %s' % (common.ugettext('Not found'), common.ugettext('WorkflowPackageState')))
    return state


def request_approval_validator(key, converted_data, errors, context):
    pass


def is_function(value: Callable):
    """
        Raises Invalid if the given value is not a function (can't be called)
    """
    if not callable(value) and not hasattr(value, "__call__"):
        raise common.Invalid(common.ugettext('Value must be a function'))
    return value


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
            except common.Invalid as e:
                pass
        raise common.Invalid(common.ugettext('Value must be one of {}'.format(list_of_validators)))

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

    log.warning("workflow_state_after_validator")

    def add_error(field_key, error):
        """
        Small helper function to add errors to the errors
        :param field_key: key of the field
        :param error: error message
        """
        errors[(field_key,)].append(error)

    if any(errors[key] for key in errors):
        # something is already wrong, so no need to do this check
        return

    pkg = context.get("package", None)

    if pkg is None:
        # let's assume we started with the default
        before_state = workflow_constants.DEFAULT_STATE.id
    else:
        before_state = workflow_helpers._get_state(pkg).id

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
            add_error(workflow_constants.DEFAULT_FIELD, common.ugettext('Missing value'))
        else:
            if before_state != after_state:
                allowed_states = workflow_constants.WORKFLOW.allowed_states(
                    context, before_state, user_id, pkg_id, owner_org, actions="assign"
                )
                if after_state not in allowed_states:
                    add_error(
                        workflow_constants.DEFAULT_FIELD,
                        common.ugettext('Value must be one of {}'.format(allowed_states))
                    )

            state = workflow_constants.WORKFLOW.get_state(after_state)
            if state.dataset_fields:
                for field in state.dataset_fields:
                    field_value = state.dataset_fields.get(field)
                    if converted_data.get((field,)) != field_value:
                        add_error(
                            field,
                            common.ugettext(
                                'The state {state} requires this field to have the value of {value}'.format(
                                    state=after_state, value=field_value
                                )
                            )
                        )
    else:
        if after_state:
            add_error(workflow_constants.DEFAULT_FIELD, common.ugettext('Value must be one of {}'.format([None])))
