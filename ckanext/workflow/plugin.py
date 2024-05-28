# encoding: utf-8

import ckan.plugins.toolkit as toolkit
from ckanext.authorization.interface import IAuthorization
from ckanext.workflow import views, helpers, utils
from ckanext.workflow.model import setup as setup_workflow_request_table, WorkflowPackageState
from ckanext.workflow.logic import validators as workflow_validators
from ckanext.workflow.logic import action as workflow_action
from ckanext.workflow.logic import auth as workflow_auth
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
    common.implements(IAuthorization, inherit=True)

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
        print(WorkflowBackend)

    # IConfigurer
    def update_config(self, config_):
        log.info("update_config")
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_resource('assets', 'ckanext-workflow')

    # IActions
    def get_actions(self):
        actions = {
            'workflow_request_list': workflow_action.get.workflow_request_list,
            'workflow_request_show': workflow_action.get.workflow_request_show,
            'workflow_state_list': workflow_action.get.workflow_state_list,
            'workflow_state_show': workflow_action.get.workflow_state_show,
            'workflow_request_create': workflow_action.create.workflow_request_create,
            'workflow_request_update': workflow_action.update.workflow_request_update,
            'workflow_state_update': workflow_action.update.workflow_state_update,
            'workflow_request_delete': workflow_action.delete.workflow_request_delete,
        }
        for key in actions:
            actions[key] = common.side_effect_free(actions[key])
        for update_action in WorkflowBackend.update_actions_dict:
            log.info("adding update_action " + update_action)
            actions[update_action] = workflow_action.workflow_action_wrapper(
                update_action, WorkflowBackend.update_actions_dict[update_action]
            )
        return actions


    # IAuthFunctions
    def get_auth_functions(self):
        auth_functions = {
            'workflow_request_list': workflow_auth.get.workflow_request_list,
            'workflow_request_show': workflow_auth.get.workflow_request_show,
            'workflow_state_list': workflow_auth.get.workflow_state_list,
            'workflow_state_show': workflow_auth.get.workflow_state_show,

            'workflow_request_create': workflow_auth.create.workflow_request_create,

            'workflow_request_update': workflow_auth.update.workflow_request_update,
            'workflow_state_update': workflow_auth.update.workflow_state_update,

            'workflow_request_delete': workflow_auth.delete.workflow_request_delete,
        }
        for update_action in WorkflowBackend.update_actions_dict:
            log.info("adding auth_function " + update_action)
            auth_functions[update_action] = workflow_auth.workflow_auth_wrapper(
                update_action, WorkflowBackend.update_actions_dict[update_action]
            )
        return auth_functions

    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprints()

    # ITemplateHelpers
    def get_helpers(self):
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

    # IAuthorization
    def get_group_capacities(self, capacities):
        capacities.update(
            {
                'banana': {
                    'permissions': capacities['editor']['permissions'],
                    'description': {'en': "I'm yellow", 'nl': 'Ik ben geel'},
                    'label': {'en': "Banana", 'nl': 'Banaan'}
                }
            }
        )
        return capacities

    def get_organization_capacities(self, capacities):
        capacities.update(
            {
                'coconut': {
                    'permissions': capacities['editor']['permissions'],
                    'description': {'en': "I'm hairy", 'nl': 'Ik ben harig'},
                    'label': {'en': "Coconut", 'nl': 'Kokosnoot'},
                    'limit': 2
                }
            }
        )
        return capacities

    def get_dataset_capacities(self, capacities):
        capacities.update(
            {
                'apple': {
                    'permissions': capacities['editor']['permissions'],
                    'description': {'en': "I'm round and juicy", 'nl': 'Ik ben rond and sappig'},
                    'label': {'en': "Apple", 'nl': 'Appel'}
                }
            }
        )
        return capacities
