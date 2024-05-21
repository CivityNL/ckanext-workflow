'''API functions for creating data from CKAN.'''
from ckanext.workflow.model.workflow_request import REQUEST_STATE_PENDING
from ckanext.workflow.interface import IWorkflowRequestController
from ckan.plugins import toolkit, PluginImplementations
from ckanext.workflow.model import WorkflowRequest, WorkflowState
import ckanext.workflow.logic.schema as workflow_schema
import ckanext.workflow.common as common

log = common.getLogger(__name__)


def workflow_request_create(context, data_dict):
    """

    :param context:
    :param data_dict:
    :return:
    """
    ###

    print("workflow_request_create workflow_request_create workflow_request_create")

    # get information from context
    model = context["model"]
    session = context["session"]
    user = context["user"]

    common.check_access('workflow_request_create', context, data_dict)

    # check if all the information given is valid
    print("before validate")
    data_dict, errors = common.navl_validate(data_dict, workflow_schema.workflow_request_create_schema(), context)
    print("after validate")
    print(f"data_dict = {data_dict}")
    print(f"errors = {errors}")
    if errors:
        raise common.ValidationError(errors)

    request = WorkflowRequest(**data_dict)
    session.add(request)
    session.flush()

    for plugin in PluginImplementations(IWorkflowRequestController):
        plugin.after_request_create(context, data_dict)

    # Create activity
    activity = model.Activity(
        request.requester.id,
        request.package.id,
        "new request",
        {
            'request': request.as_dict(),
            'actor': request.requester.name if request.requester else None
        }
    )
    session.add(activity)

    if not context.get('defer_commit'):
        model.repo.commit()

    return request.as_dict()
