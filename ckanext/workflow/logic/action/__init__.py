import ckanext.workflow.logic.action.get as get
import ckanext.workflow.logic.action.create as create
import ckanext.workflow.logic.action.delete as delete
import ckanext.workflow.logic.action.update as update
from ckanext.workflow.backend import WorkflowBackend

from ckanext.workflow.model import WorkflowPackageState
from ckanext.workflow.common import chained_action, getLogger, g, get_action, h

log = getLogger(__name__)


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
                    get_action('workflow_state_update')(workflow_state_update_context, workflow_state_update_data_dict)

        return result

    return workflow_action
