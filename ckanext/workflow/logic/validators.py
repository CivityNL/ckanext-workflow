from typing import Dict, Callable
import ckan.model as model
from ckanext.workflow.backend import WorkflowBackend
from ckanext.workflow.model import WorkflowRequest, WorkflowState, WorkflowMessage
from ckanext.workflow.model.workflow_request import REQUEST_STATE_PENDING, REQUEST_STATE_APPROVED, \
    REQUEST_STATE_REJECTED
import ckanext.workflow.common as common
import ckanext.workflow.helpers as helpers
# logging
import logging

log = logging.getLogger(__name__)

unicode_only = common.get_validator("unicode_only")
one_of = common.get_validator("one_of")
empty = common.get_validator("empty")
default = common.get_validator("default")


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
        state_id = helpers._get_state_id(package_id)
        workflow_transition = WorkflowBackend.get_transition(state_id, request_state)

        if not process_message and process_state in WorkflowRequest.states(handled=True):
            if process_state == REQUEST_STATE_APPROVED and workflow_transition.get('approve_message_required'):
                errors[(process_message_field,)].append(
                    common.ugettext('Process state "{}" requires a process_message').format(process_state)
                )
            if process_state == REQUEST_STATE_REJECTED and workflow_transition.get('reject_message_required'):
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
        if process_state not in WorkflowRequest.states(open=True):
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
        state_id = helpers._get_state_id(package_id)
        workflow_transition = WorkflowBackend.get_transition(state_id, request_state)

        if not workflow_transition:
            errors[(request_state_field,)].append(
                common.ugettext('No transition exists from state "{}" to state "{}"').format(request_state, state_id))

    return _transition_exists


def has_error(field, errors):
    return len(errors.get((field,))) > 0


def request_message_required(
        package_id_field='package_id', request_state_field='request_state', request_message_field='request_message'
):
    def _request_message_required(key, data, errors, context):
        print(f"_request_message_required -> {data}")
        package_id = data.get((package_id_field,))
        request_state = data.get((request_state_field,))
        request_message = data.get((request_message_field,))
        print(f"_request_message_required - {has_errors([package_id_field, request_state_field], errors)}")
        if has_errors([package_id_field, request_state_field], errors):
            return
        state_id = helpers._get_state_id(package_id)
        workflow_transition = WorkflowBackend.get_transition(state_id, request_state)

        if workflow_transition and workflow_transition.get('request_message_required'):
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
    query = session.query(WorkflowRequest).filter_by(**filter_kwargs)
    if query.first() is not None:
        raise common.Invalid(common.ugettext('request_does :: Request id already exists'))


def default_current_user(key, data, errors, context):
    print("default_current_user")
    value = data.get(key)
    if value is None or value == '' or value is common.missing:
        data[key] = context["user"]


def workflow_state_exists_for_package(package_id: str) -> str:
    """
        Returns:
            the given value if a WorkflowRequest identified by the request_id can be found
        Raises:
            Invalid if not found
    """
    result = WorkflowState.get(package_id)
    if not result:
        raise common.Invalid(common.ugettext('Package does not have a WorkflowState'))
    return package_id


def workflow_state_does_not_exist_for_package(package_id: str) -> str:
    """
        Returns:
            the given value if a WorkflowRequest identified by the request_id can be found
        Raises:
            Invalid if not found
    """
    result = WorkflowState.get(package_id)
    if result:
        raise common.Invalid(common.ugettext('Package does have a WorkflowState'))
    return package_id


def request_id_does_not_exist(request_id: str) -> str:
    """
        Returns:
            the given value if a WorkflowRequest identified by the request_id can be found
        Raises:
            Invalid if not found
    """
    result = WorkflowRequest.get(request_id)
    if result:
        raise common.Invalid(common.ugettext('Request id already exists'))
    return request_id


def workflow_message_exists(message_id: str) -> str:
    result = WorkflowMessage.get(message_id)
    if not result:
        raise common.Invalid(common.ugettext('Message does not exists'))
    return message_id


def request_id_exists(request_id: str) -> str:
    """
        Returns:
            the given value if a WorkflowRequest identified by the request_id can be found
        Raises:
            Invalid if not found
    """
    result = WorkflowRequest.get(request_id)
    if not result:
        raise common.Invalid(common.ugettext('Request id does not exist'))
    return request_id


def organization_id_exists(organization_id: str) -> str:
    """
        Raises Invalid if an organization identified by the id cannot be found
    """

    result = model.Group.get(organization_id)
    if not result or not result.is_organization:
        raise common.Invalid('%s: %s' % (common.ugettext('Not found'), common.ugettext('Organization')))
    return result.id


def state_exists(state):
    """

    :param state:
    :return:
    """
    if state not in WorkflowBackend.get_states():
        raise common.Invalid('%s: %s' % (common.ugettext('Not found'), common.ugettext('WorkflowState')))
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


def list_validator(validator):
    """
    Validates a list of values, each value validated using the validator
    """
    def _list_validator(value):
        if not isinstance(value, list):
            value = [value]
        return [validator(v) for v in value]

    return _list_validator


def list_one_of(list_of_values):
    """
    Validates a list of values, each value requiring to be 'one_of' the given list of values
    """
    return list_validator(one_of(list_of_values))


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



###

def message_exists(message_id):
    message = WorkflowMessage.get(message_id)
    print(f"found {message} for {message_id}")
    if message is None:
        raise common.Invalid('%s: %s' % (common.ugettext('Not found'), common.ugettext('WorkflowMessage')))
    return message_id


def reference_object_exists(key, data, errors, context):
    session = context["session"]
    if has_errors(['reference_type', 'reference_id'], errors):
        return

    object_type = data.get(('reference_type',))
    object_id = data.get(('reference_id',))
    print(f"{object_type} {object_id}")
    if not object_type or not object_id:
        return

    obj = None
    if object_type == 'package':
        obj = model.Package.get(object_id)
    if object_type == 'workflow_request':
        obj = WorkflowRequest.get(object_id)
    if object_type == 'workflow_message':
        obj = WorkflowMessage.get(object_id)
    if obj is None:
        raise common.Invalid(common.ugettext('reference_object_exists is not true'))
