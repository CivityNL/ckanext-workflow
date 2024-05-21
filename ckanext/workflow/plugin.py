# encoding: utf-8

import ckan.plugins.toolkit as toolkit
from ckanext.authorization.interface import IAuthorization
from ckanext.workflow import views, helpers, utils
from ckanext.workflow.model import setup as setup_workflow_request_table, WorkflowState
from ckanext.workflow.logic import validators as workflow_validators
from ckanext.workflow.logic import action as workflow_action
from ckanext.workflow.logic import auth as workflow_auth
from ckanext.workflow.backend import WorkflowBackend
import ckanext.workflow.constants as workflow_constants
from ckanext.workflow.utils import default_getter
from ckanext.workflow.common import getLogger, model, SingletonPlugin
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
        log.warning("Adding side_effect_free to all actions")
        for key in actions:
            actions[key] = common.side_effect_free(actions[key])
        return actions


    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'workflow_request_list': workflow_auth.get.workflow_request_list,
            'workflow_request_show': workflow_auth.get.workflow_request_show,
            'workflow_state_list': workflow_auth.get.workflow_state_list,
            'workflow_state_show': workflow_auth.get.workflow_state_show,

            'workflow_request_create': workflow_auth.create.workflow_request_create,

            'workflow_request_update': workflow_auth.update.workflow_request_update,
            'workflow_state_update': workflow_auth.update.workflow_state_update,

            'workflow_request_delete': workflow_auth.delete.workflow_request_delete,
        }

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
            'workflow_choices_helper': helpers.workflow_choices_helper
        }
        return workflow_helpers

    # IFacets:
    def dataset_facets(self, facets_dict, package_type):
        facets_dict['workflow_state_id'] = common.ugettext('Workflow')
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        facets_dict['workflow_state_id'] = common.ugettext('Workflow')
        return facets_dict

    # IPackageController
    def before_index(self, pkg_dict):
        log.warning("before_index")
        package_id = pkg_dict.get("id")
        workflow_state = WorkflowState.get(package_id)
        pkg_dict["workflow_state_id"] = workflow_state.state_id if workflow_state else None
        return pkg_dict

    def read(self, entity):
        log.warning("read")
        pass

    def create(self, entity):
        log.warning("create")
        pass

    def edit(self, entity):
        log.warning("edit")
        pass

    def delete(self, entity):
        log.warning("delete")
        pass

    def after_create(self, context, pkg_dict):
        log.warning("after_create")
        pass

    def after_update(self, context, pkg_dict):
        log.warning("after_update")
        pass

    def after_delete(self, context, pkg_dict):
        log.warning("after_delete")
        pass

    def after_show(self, context, pkg_dict):
        log.warning("after_show")
        package_id = pkg_dict.get("id")
        workflow_state = WorkflowState.get(package_id)
        pkg_dict["workflow"] = workflow_state.as_dict() if workflow_state else None
        pass

    def before_search(self, search_params):
        log.warning("before_search")
        return search_params

    def after_search(self, search_results, search_params):
        log.warning("after_search")
        return search_results

    def before_view(self, pkg_dict):
        log.warning("before_view")
        return pkg_dict

    # def after_update(self, context, data):
    #     is_workflow_set_state = data.pop('is_workflow_set_state', False)
    #     context['workflow_set_state'] = is_workflow_set_state

    # def after_search(self, search_results, data_dict):
    #
    #     if workflow_constants.DEFAULT_FIELD in search_results['search_facets']:
    #         items = search_results['search_facets'][workflow_constants.DEFAULT_FIELD]['items']
    #         items = [dict(item, display_name=workflow_constants.WORKFLOW.get_state(item["name"]).label) for item in
    #                  items]
    #         search_results['search_facets'][workflow_constants.DEFAULT_FIELD]['items'] = items
    #
    #     return search_results

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
