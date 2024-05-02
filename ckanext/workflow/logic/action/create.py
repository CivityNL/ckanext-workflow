'''API functions for creating data from CKAN.'''

from ckanext.workflow.plugin.interfaces import IWorkflowRequestController
from ckan.plugins import toolkit, PluginImplementations
from ckanext.workflow.model import WorkflowRequest
import ckanext.workflow.logic.schema as workflow_schema


def workflow_request_create(context, data_dict):
    """

    :param context:
    :param data_dict:
    :return:
    """
    ###
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

    for plugin in PluginImplementations(IWorkflowRequestController):
        plugin.before_request_create(context, request_dict)

    request = WorkflowRequest(**request_dict)
    request.save()

    for plugin in PluginImplementations(IWorkflowRequestController):
        plugin.after_request_create(context, request_dict)
    return request.as_dict()
