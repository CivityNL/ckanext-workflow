from ckanext.workflow.backend import WorkflowBackend
from ckanext.workflow.model import WorkflowPackageState
from ckanext.workflow.common import (
    chained_auth_function, chained_action, getLogger, g, get_action, h, navl_validate, ValidationError, check_access
)
import ckanext.workflow.logic.schema as workflow_schema

log = getLogger(__name__)

def workflow_action_schema_decorator(action_function):
    def workflow_action_schema_wrapper(context, data_dict):
        schema = getattr(workflow_schema, "{}_schema".format(action_function.__name__))()
        validated_data_dict, errors = navl_validate(data_dict, schema, context)
        if errors:
            raise ValidationError(errors)
        check_access(action_function.__name__, context, validated_data_dict)
        return action_function(context, validated_data_dict)

    workflow_action_schema_wrapper.__name__ = action_function.__name__
    workflow_action_schema_wrapper.__module__ = action_function.__module__
    workflow_action_schema_wrapper.__doc__ = "@decorated with :py:func:`~{}.{}`\n{}".format(
        __name__, workflow_action_schema_decorator.__name__, action_function.__doc__
    )

    return workflow_action_schema_wrapper

def workflow_action_wrapper(action, getter):
    @chained_action
    def workflow_action(original_action, context, data_dict):
        result = original_action(context, data_dict)
        package_ids = getter(context, data_dict)
        for package_id in package_ids:
            workflow_package_state = WorkflowPackageState.get(package_id)
            if h.workflow_enabled_for_organization(workflow_package_state.package.owner_org):
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
            if h.workflow_enabled_for_organization(workflow_package_state.package.owner_org):
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
