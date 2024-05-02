# encoding: utf-8

'''Constants.'''

import os
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.workflow import views, helpers, utils
import ckan.lib.plugins as lib_plugins
from ckan.lib.plugins import DefaultTranslation
from ckanext.workflow.model import setup as setup_workflow_request_table
from ckanext.workflow.logic import validators as workflow_validators
from ckanext.workflow.logic import action as workflow_action
from ckanext.workflow.logic import auth as workflow_auth
import logging
from ckanext.workflow.backend import Workflow
import ckan.model as model
import ckanext.workflow.constants as workflow_constants

log = logging.getLogger(__name__)

tk_add_template_directory = toolkit.add_template_directory
# noinspection PyProtectedMember
tk_ = toolkit._


class WorkflowPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IValidators
    def get_validators(self):
        return {
            'workflow_organization_id_exists': workflow_validators.organization_id_exists,
            'workflow_request_id_does_not_exist': workflow_validators.request_id_does_not_exist,
            'workflow_state_exists': workflow_validators.state_exists,
            'workflow_request_approval_validator': workflow_validators.request_approval_validator,
            'workflow_state_after_validator': workflow_validators.workflow_state_after_validator
        }

    def i18n_directory(self):
        path = os.path.abspath(
            os.path.join(
                super(WorkflowPlugin, self).i18n_directory(),
                '..', '..', 'i18n'
            )
        )
        return path

    # IConfigurable
    def configure(self, config):
        context = {'model': model, 'session': model.Session}

        setup_workflow_request_table()

        self.roles = utils.get_roles(context)
        workflow_constants.CAPACITIES = list(self.roles.keys())
        workflow_constants.PERMISSIONS = [f"{workflow_constants.PERMISSION_PREFIX}{permission}" for permissions in
                                          self.roles.values() for permission in permissions]

        _role_stuff = workflow_constants.CAPACITIES + workflow_constants.PERMISSIONS
        workflow_constants.WORKFLOW = Workflow(utils.get_states(context, _role_stuff))
        states = workflow_constants.WORKFLOW.get_states()
        workflow_constants.WORKFLOW.set_default_state(utils.get_default_state(context, states))
        workflow_constants.WORKFLOW.set_transitions(utils.get_transitions(context, _role_stuff, states))
        workflow_constants.WORKFLOW.set_update_actions(utils.get_update_actions(context))

        # package_plugin: plugins.IDatasetForm
        # # noinspection PyProtectedMember
        # for package_type in lib_plugins._package_plugins:
        #     # noinspection PyProtectedMember
        #     package_plugin = lib_plugins._package_plugins[package_type]

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, '../templates')

    # IActions
    def get_actions(self):
        workflow_actions = {
            'workflow_set_state': workflow_action.update.workflow_set_state,
            'workflow_request_show': workflow_action.get.workflow_request_show,
            'workflow_request_list': workflow_action.get.workflow_request_list,
            'workflow_request_create': workflow_action.create.workflow_request_create,
            'workflow_request_update': workflow_action.update.workflow_request_update,
            'workflow_request_delete': workflow_action.delete.workflow_request_delete,
        }
        update_actions = workflow_constants.WORKFLOW.update_actions
        for action in update_actions:
            workflow_actions[action] = workflow_action.workflow_chained_action(action, update_actions.get(action))
        return workflow_actions

    # IAuthFunctions
    def get_auth_functions(self):
        workflow_auth_functions = {}
        update_actions = workflow_constants.WORKFLOW.update_actions
        for action in update_actions:
            workflow_auth_functions[action] = workflow_auth.workflow_chained_auth_function(action,
                                                                                           update_actions.get(action))
        return workflow_auth_functions

    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprints()

    # ITemplateHelpers
    def get_helpers(self):
        workflow_helpers = {
            'workflow_get_states': lambda: [(state.id, state.label) for state in workflow_constants.WORKFLOW.states],
            'workflow_get_transitions': lambda: [(transition.id, transition.label) for transition in
                                                 workflow_constants.WORKFLOW.transitions],
            'workflow_get_roles': lambda: self.roles,
            'workflow_get_allowed_states': helpers.get_allowed_states,
            'workflow_get_state_label': helpers.get_state_label,
            'workflow_show_notice_to_be_unpublished_on_edit': helpers.show_notice_to_be_unpublished_on_edit,
            'workflow_choices_helper': helpers.workflow_choices_helper
        }
        return workflow_helpers

    # IFacets:
    def dataset_facets(self, facets_dict, package_type):
        facets_dict[workflow_constants.DEFAULT_FIELD] = toolkit._('Workflow')
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        facets_dict[workflow_constants.DEFAULT_FIELD] = toolkit._('Workflow')
        return facets_dict

    # IPackageController
    def after_update(self, context, data):
        is_workflow_set_state = data.pop('is_workflow_set_state', False)
        context['workflow_set_state'] = is_workflow_set_state

    def after_search(self, search_results, data_dict):

        if workflow_constants.DEFAULT_FIELD in search_results['search_facets']:
            items = search_results['search_facets'][workflow_constants.DEFAULT_FIELD]['items']
            items = [dict(item, display_name=workflow_constants.WORKFLOW.get_state(item["name"]).label) for item in
                     items]
            search_results['search_facets'][workflow_constants.DEFAULT_FIELD]['items'] = items

        return search_results
