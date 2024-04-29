'''API functions for creating data from CKAN.'''

from ckanext.workflow.plugin.interface import IWorkflowRequestController
from ckan.plugins import toolkit, PluginImplementations
from ckanext.workflow.model import WorkflowRequest
import ckanext.workflow.logic.schema as workflow_schema

tk_chained_action = toolkit.chained_action


@tk_chained_action
def package_create(original_action, context, data_dict):
    print("chained_action package_create")
    return original_action(context, data_dict)


def workflow_request_create(context, data_dict):
	###
    print(f"workflow_request_create with {data_dict}")
    model = context["model"]
    session = context["session"]
    user = context["user"]

    # fill 
    if 'request_user_id' not in data_dict or not data_dict['request_user_id']:
         data_dict['request_user_id'] = user

    schema = workflow_schema.workflow_request_create_schema()

    request_dict, errors = toolkit.navl_validate(data_dict, schema, context)
    if errors:
        session.rollback()
        raise toolkit.ValidationError(errors)

    plugin: IWorkflowRequestController
    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.before_request_create(context, request_dict)

    request = WorkflowRequest(**request_dict)
    request.save()

    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.after_request_create(context, request_dict)
    return request.as_dict()
	