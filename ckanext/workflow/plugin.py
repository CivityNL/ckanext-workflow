# encoding: utf-8

import ckan.plugins.toolkit as toolkit
from ckanext.workflow import views, helpers
from ckanext.workflow.model import setup as setup_workflow_request_table, WorkflowPackageState
from ckanext.workflow.logic import validators as workflow_validators
from ckanext.workflow.logic import action as workflow_action
from ckanext.workflow.logic import auth as workflow_auth
import ckanext.workflow.logic as workflow_logic
from ckanext.workflow.backend import WorkflowBackend
import ckanext.workflow.constants as workflow_constants
from ckanext.workflow.common import getLogger, model, SingletonPlugin, h, ValidationError
import ckanext.workflow.common as common
# # logging
# import logging
log = getLogger(__name__)

tk_add_template_directory = toolkit.add_template_directory
# noinspection PyProtectedMember
tk_ = toolkit._


class WorkflowPlugin(common.SingletonPlugin, common.DefaultTranslation):
    common.implements(common.ITranslation)
    common.implements(common.IConfigurable)
    common.implements(common.IConfigurer)
    common.implements(common.IActions)
    common.implements(common.IAuthFunctions)
    common.implements(common.ITemplateHelpers)
    common.implements(common.IBlueprint)
    common.implements(common.IValidators)
    common.implements(common.IFacets)
    common.implements(common.IPackageController, inherit=True)

    WORKFLOW_PACKAGE_STATE_ID_FIELD = 'workflow_package_state_id'

    # IValidators
    def get_validators(self):
        return {
            'workflow_organization_id_exists': workflow_validators.organization_id_exists,
            'workflow_request_id_does_not_exist': workflow_validators.request_id_does_not_exist,
            'workflow_state_exists': workflow_validators.state_exists,
            'workflow_request_approval_validator': workflow_validators.request_approval_validator,
            'workflow_state_after_validator': workflow_validators.workflow_state_after_validator
        }

    # IConfigurable
    def configure(self, config):
        log.info("configure")
        setup_workflow_request_table()
        WorkflowBackend.setup()

    # IConfigurer
    def update_config(self, config_):
        log.info("update_config")
        common.add_template_directory(config_, 'templates')
        common.add_resource('assets', 'ckanext-workflow')

    # IActions
    def get_actions(self):
        actions = {
            'workflow_dataset_request_list': workflow_action.workflow_dataset_request_list,
            'workflow_dataset_request_show': workflow_action.workflow_dataset_request_show,
            'workflow_dataset_request_create': workflow_action.workflow_dataset_request_create,
            'workflow_dataset_request_update': workflow_action.workflow_dataset_request_update,
            'workflow_dataset_request_delete': workflow_action.workflow_dataset_request_delete,
            'workflow_dataset_state_update': workflow_action.workflow_dataset_state_update,
        }
        for update_action in WorkflowBackend.update_actions_dict:
            log.info("adding update_action " + update_action)
            actions[update_action] = workflow_logic.workflow_action_wrapper(
                update_action, WorkflowBackend.update_actions_dict[update_action]
            )
        return actions


    # IAuthFunctions
    def get_auth_functions(self):
        """
        Implementation of :py:meth:`ckan.plugins.interfaces.IAuthFunctions.get_auth_functions`
        :return:
        """
        auth_functions = {
            'workflow_dataset_request_list': workflow_auth.workflow_dataset_request_list,
            'workflow_dataset_request_show': workflow_auth.workflow_dataset_request_show,
            'workflow_dataset_request_create': workflow_auth.workflow_dataset_request_create,
            'workflow_dataset_request_update': workflow_auth.workflow_dataset_request_update,
            'workflow_dataset_request_delete': workflow_auth.workflow_dataset_request_delete,
            'workflow_dataset_state_update': workflow_auth.workflow_dataset_state_update,
        }
        for update_action in WorkflowBackend.update_actions_dict:
            auth_functions[update_action] = workflow_logic.workflow_auth_wrapper(
                update_action, WorkflowBackend.update_actions_dict[update_action]
            )
        return auth_functions

    def get_blueprint(self):
        """
        Implementation of :py:meth:`ckan.plugins.interfaces.IBlueprint.get_blueprint`
        :return:
        """
        return views.get_blueprints()

    def get_helpers(self):
        """
        Implementation of :py:meth:`ckan.plugins.interfaces.ITemplateHelpers.get_helpers`
        :return:
        """
        workflow_helpers = {
            'workflow_get_states': lambda: [(state.id, state.label) for state in workflow_constants.WORKFLOW.states],
            'workflow_get_transitions': lambda: [(transition.id, transition.label) for transition in
                                                 workflow_constants.WORKFLOW.transitions],
            'workflow_get_allowed_states': helpers.get_allowed_states,
            'workflow_get_state_label': helpers.get_state_label,
            'workflow_show_notice_to_be_unpublished_on_edit': helpers.show_notice_to_be_unpublished_on_edit,
            'workflow_choices_helper': helpers.workflow_choices_helper,
            'workflow_package_request_count': helpers.package_request_count,
            'workflow_enabled_for_organization': helpers.workflow_enabled_for_organization
        }
        return workflow_helpers

    # IFacets:
    def dataset_facets(self, facets_dict, package_type):
        facets_dict[self.WORKFLOW_PACKAGE_STATE_ID_FIELD] = common.ugettext('Workflow')
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        facets_dict[self.WORKFLOW_PACKAGE_STATE_ID_FIELD] = common.ugettext('Workflow')
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        facets_dict[self.WORKFLOW_PACKAGE_STATE_ID_FIELD] = common.ugettext('Workflow')
        return facets_dict

    # IPackageController
    def before_index(self, pkg_dict):
        log.warning("before_index")
        package_id = pkg_dict.get("id")
        workflow_state = WorkflowPackageState.get(package_id)
        pkg_dict[self.WORKFLOW_PACKAGE_STATE_ID_FIELD] = workflow_state.state_id if workflow_state else None
        log.warning(f"before_index pkg_dict[{self.WORKFLOW_PACKAGE_STATE_ID_FIELD}] = {pkg_dict[self.WORKFLOW_PACKAGE_STATE_ID_FIELD]}")
        return pkg_dict

    def after_create(self, context, pkg_dict):
        pass
        # if h.workflow_enabled_for_organization(pkg_dict.get("owner_org", None)):
        #     workflow_state_update_context = dict(context, defer_commit=True)
        #     workflow_state_update_data_dict = {
        #         'package_id': pkg_dict.get("id"),
        #         'state_id': WorkflowBackend.default_state
        #     }
        #     common.get_action('workflow_state_update')(workflow_state_update_context, workflow_state_update_data_dict)

    def after_update(self, context, pkg_dict):
        pass
        # log.warning("after_update")
        # if h.workflow_enabled_for_organization(pkg_dict.get("owner_org", None)):
        #     session = context["session"]
        #     workflow_state = WorkflowPackageState.get(pkg_dict.get("id"))
        #     print(workflow_state)
        #     if workflow_state is None:
        #         errors = 'workflow_state is None'
        #     else:
        #         errors = WorkflowBackend.get_state(workflow_state.state_id).validate(pkg_dict)
        #     if errors:
        #         session.rollback()
        #         raise ValidationError(errors)

    def after_show(self, context, pkg_dict):
        log.warning("after_show")
        package_id = pkg_dict.get("id")
        workflow_state = WorkflowPackageState.get(package_id)
        pkg_dict["workflow"] = workflow_state.as_dict() if workflow_state else None
        pass

    def after_search(self, search_results, search_params):
        if self.WORKFLOW_PACKAGE_STATE_ID_FIELD in search_results['search_facets']:
            items = search_results['search_facets'][self.WORKFLOW_PACKAGE_STATE_ID_FIELD]['items']
            items = [
                dict(item, display_name=WorkflowBackend.get_state(item["name"]).label) for item in items
            ]
            search_results['search_facets'][self.WORKFLOW_PACKAGE_STATE_ID_FIELD]['items'] = items

        return search_results
