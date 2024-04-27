from ckan.authz import users_role_for_group_or_org
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.workflow import views, helpers, utils
from ckanext.workflow.logic import action, auth
from ckan.lib.plugins import DefaultTranslation
from ckanext.workflow.model import setup as setup_workflow_request_table
from ckanext.workflow.logic import validators as workflow_validators
from ckanext.workflow.logic import action as workflow_action
import logging
from ckanext.workflow.logic.interface import Workflow
import ckan.model as model
import ckanext.workflow.constants as workflow_constants

log = logging.getLogger(__name__)

def get_workflow_state(context, pkg_name_or_id):
    pkg_dict = {} if pkg_name_or_id is None else toolkit.get_action("package_show")(context, {"id": pkg_name_or_id})
    # request = toolkit.get_action("workflow_request_show")(context, {"id": pkg_name_or_id})
    role = users_role_for_group_or_org(pkg_dict.get("owner_org"), context.get("user"))
    return dict({k: pkg_dict[k] for k in  pkg_dict}, role=role)


@toolkit.chained_action
def package_create(original_action, context, data_dict):
    print("chained_action package_create")
    return original_action(context, data_dict)


@toolkit.chained_action
def package_update(original_action, context, data_dict):
    print("chained_action package_update")
    return original_action(context, data_dict)

@toolkit.chained_auth_function
@toolkit.auth_sysadmins_check
def auth_package_update(next_auth, context, data_dict=None):
    print("chained_auth_function package_update")
    return next_auth(context, data_dict)


class WorkflowPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IValidators)


    # IValidators
    def get_validators(self):
        return {
            'workflow_organization_id_exists': workflow_validators.organization_id_exists,
            'workflow_request_id_does_not_exist': workflow_validators.request_id_does_not_exist,
            'workflow_request_state_exists': workflow_validators.request_state_exists,
            'workflow_request_approval_validator': workflow_validators.request_approval_validator
        }

    # IConfigurable
    def configure(self, config):  
        context = {'model': model, 'session': model.Session}

        setup_workflow_request_table()

        self.roles = utils.get_roles(context)
        workflow_constants.CAPACITIES = list(self.roles.keys())
        workflow_constants.PERMISSIONS = [f"{workflow_constants.PERMISSION_PREFIX}{permission}" for permissions in self.roles.values() for permission in permissions]

        _role_stuff = workflow_constants.CAPACITIES + workflow_constants.PERMISSIONS
        workflow_constants.WORKFLOW = Workflow(utils.get_states(context, _role_stuff))
        states = workflow_constants.WORKFLOW.get_states()
        workflow_constants.WORKFLOW.set_default_state(utils.get_default_state(context, states))
        workflow_constants.WORKFLOW.set_transitions(utils.get_transitions(context, _role_stuff, states))


    # IConfigurer
    def update_config(self, config_):  
        toolkit.add_template_directory(config_, 'templates')

    # IActions
    def get_actions(self):
        return {
            'workflow_package_set_state': action.package_set_state,
            ####
            # 'package_create': package_create,
            # 'package_update': package_update,
            'workflow_request_show': workflow_action.workflow_request_show,
            'workflow_request_list': workflow_action.workflow_request_list,
            'workflow_request_create': workflow_action.workflow_request_create,
            'workflow_request_update': workflow_action.workflow_request_update,
            'workflow_request_delete': workflow_action.workflow_request_delete,
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'workflow_package_set_state': auth.package_set_state,
            'package_update': auth_package_update
        }

    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprints()

    # ITemplateHelpers
    def get_helpers(self):   
        workflow_helpers = {
            'workflow_get_states': lambda : [(state.id, state.label) for state in workflow_constants.WORKFLOW.states],
            'workflow_get_transitions': lambda : [(transition.id, transition.label) for transition in workflow_constants.WORKFLOW.transitions],
            'workflow_get_roles': lambda : self.roles,
            'workflow_get_allowed_states': helpers.get_allowed_states,
            'workflow_get_state_label': helpers.get_state_label,
            'workflow_show_notice_to_be_unpublished_on_edit': helpers.show_notice_to_be_unpublished_on_edit
        }
        return workflow_helpers
