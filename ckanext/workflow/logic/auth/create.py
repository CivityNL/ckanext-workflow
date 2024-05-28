'''API functions for creating data from CKAN.'''

from ckanext.workflow.interface import IWorkflowPackageRequestController
from ckan.plugins import toolkit, PluginImplementations
from ckanext.workflow.model import WorkflowPackageRequest, WorkflowPackageState
import ckanext.workflow.logic.schema as workflow_schema
import ckanext.workflow.common as common
log = common.getLogger(__name__)


def workflow_request_create(context, data_dict):

    data_dict, errors = common.navl_validate(data_dict, workflow_schema.workflow_request_create_schema(), context)

    user = context['auth_user_obj']
    request_fields = ['package_id', 'request_user_id', 'request_state']

    if any(field in errors for field in request_fields):
        raise common.ValidationError(errors)

    package_id, request_user_id, request_state = common.get_or_bust(data_dict, request_fields)
    workflow_state = WorkflowPackageState.get(package_id)
    owner_org = workflow_state.package.owner_org
    state_id = workflow_state.state_id

    print(common.users_role_for_group_or_org(owner_org, user.name))

    # package_id
    # request_user_id
    # request_state

    # what do we need for this to work?
    #

    log.warning("AUTH workflow_request_create still needs to be implemented")

    return {'success': True}
