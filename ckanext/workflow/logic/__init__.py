from ckanext.workflow.backend import WorkflowBackend
from ckanext.workflow.model import WorkflowPackageState
from ckanext.workflow.common import (
    chained_auth_function, chained_action, getLogger, g, get_action, h, navl_validate, ValidationError, check_access
)
import ckanext.workflow.logic.schema as workflow_schema
from ckanext.workflow.utils import sphinx_decorator

log = getLogger(__name__)


def workflow_action_schema_decorator(action_function):
    '''
    This decorator can be used for actions which have a schema for validating the `data_dict` argument.
    '''

    schema_name = "{}_schema".format(action_function.__name__)

    def workflow_action_schema_wrapper(context, data_dict):
        '''
        Validates the `data_dict` by using the schema following the naming convention
        `{action_function.__name__}_schema` and passing it to the action function.
        '''
        if not hasattr(workflow_schema, schema_name):
            raise ValueError(f"{schema_name} does not exist")
        schema = getattr(workflow_schema, schema_name)()
        validated_data_dict, errors = navl_validate(data_dict, schema, context)
        if errors:
            raise ValidationError(errors)
        check_access(action_function.__name__, context, validated_data_dict)
        return action_function(context, validated_data_dict)

    # making sure decorated methods are handled correctly by Sphinx and prepend the docstring with a mention
    extra_message = "See also :py:func:`~ckanext.workflow.logic.schema.{}` for the schema used.".format(schema_name)
    sphinx_decorator(workflow_action_schema_decorator, workflow_action_schema_wrapper, action_function, extra_message)

    return workflow_action_schema_wrapper


def workflow_action_wrapper(action, getter):
    @chained_action
    def workflow_action(original_action, context, data_dict):
        result = original_action(context, data_dict)
        package_ids = getter(context, data_dict)
        for package_id in package_ids:
            workflow_package_state = WorkflowPackageState.get(package_id)
            workflow_state = WorkflowBackend.get_state(workflow_package_state.state_id)
            state_after_update_action = workflow_state.state_after_update_action(
                action, g.userobj.id, package_id
            )
            if state_after_update_action != workflow_package_state.state_id:
                workflow_state_update_context = dict(context, ignore_auth=True)
                workflow_state_update_data_dict = {
                    'package_id': package_id,
                    'state_id': state_after_update_action
                }
                get_action('workflow_dataset_state_update')(workflow_state_update_context, workflow_state_update_data_dict)

        return result

    return workflow_action


def workflow_auth_wrapper(action, getter):
    @chained_auth_function
    def workflow_auth(original_auth, context, data_dict):
        result = original_auth(context, data_dict)
        if not result.get("success"):
            return result
        package_ids = getter(context, data_dict)
        for package_id in package_ids:
            workflow_package_state = WorkflowPackageState.get(package_id)
            workflow_state = WorkflowBackend.get_state(workflow_package_state.state_id)
            update_action_allowed = workflow_state.update_action_allowed(
                action, g.userobj.id, package_id
            )
            if not update_action_allowed:
                result = {
                    "success": False
                }
                return result
        return result

    return workflow_auth
