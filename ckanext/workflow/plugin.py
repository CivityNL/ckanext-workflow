import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.workflow import views, helpers, utils
from ckanext.workflow.logic import action, auth
from ckan.lib.plugins import DefaultTranslation


class WorkflowPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # IActions
    def get_actions(self):
        return {
            'workflow_package_publish': action.package_publish,
            'workflow_package_unpublish': action.package_unpublish
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'workflow_package_publish': auth.package_publish,
            'workflow_package_unpublish': auth.package_unpublish
        }

    # IBlueprint
    def get_blueprint(self):
        return views.get_blueprints()

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'workflow_show_publish_button': helpers.show_publish_button,
            'workflow_show_unpublish_button': helpers.show_unpublish_button,
            'workflow_show_notice_to_be_unpublished_on_edit': helpers.show_notice_to_be_unpublished_on_edit
        }

    # IPackageController
    def after_create(self, context, data_dict):
        if utils.show(data_dict, False, 'workflow_package_publish', False, context):
            toolkit.get_action("workflow_package_unpublish")({'user': context.get('user')}, {'id': data_dict.get('id')})


    def after_update(self, context, data_dict):
        self.after_create(context, data_dict)
