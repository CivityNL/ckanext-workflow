# encoding: utf-8

# This file contains commonly used parts of external libraries. The idea is
# to help in removing helpers from being used as a dependency by many files
# but at the same time making it easy to change for example the json lib
# used.

import logging as _logging

getLogger = _logging.getLogger

from ckan import model as _model
import ckan.lib.plugins as _lib_plugins
import ckan.plugins as _plugins
import ckan.logic.auth as _logic_auth
import ckan.authz as _authz
import ckan.lib.dictization.model_dictize as _lib_model_dictize


users_role_for_group_or_org = _authz.users_role_for_group_or_org
has_user_permission_for_group_or_org = _authz.has_user_permission_for_group_or_org
user_is_collaborator_on_dataset = _authz.user_is_collaborator_on_dataset
is_sysadmin = _authz.is_sysadmin
get_user_id_for_username = _authz.get_user_id_for_username
auth_is_anon_user = _authz.auth_is_anon_user
has_user_permission_for_some_org = _authz.has_user_permission_for_some_org

group_dictize = _lib_model_dictize.group_dictize
group_list_dictize = _lib_model_dictize.group_list_dictize


DefaultTranslation = _lib_plugins.DefaultTranslation
SingletonPlugin = _plugins.SingletonPlugin
implements = _plugins.implements
PluginImplementations = _plugins.PluginImplementations
model = _model
get_package_object = _logic_auth.get_package_object
ITranslation = _plugins.ITranslation
IConfigurable = _plugins.IConfigurable
IConfigurer = _plugins.IConfigurer
IActions = _plugins.IActions
IAuthFunctions = _plugins.IAuthFunctions
ITemplateHelpers = _plugins.ITemplateHelpers
IBlueprint = _plugins.IBlueprint
IValidators = _plugins.IValidators
IFacets = _plugins.IFacets
IPackageController = _plugins.IPackageController
