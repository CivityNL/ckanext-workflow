# logging
import logging
log = logging.getLogger(__name__)

import ckanext.workflow.logic.auth.get as get
import ckanext.workflow.logic.auth.create as create
import ckanext.workflow.logic.auth.delete as delete
import ckanext.workflow.logic.auth.update as update

from ckanext.workflow.backend import WorkflowBackend
from ckanext.workflow.model import WorkflowPackageState
from ckanext.workflow.common import chained_auth_function, getLogger, g, h

log = getLogger(__name__)

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
