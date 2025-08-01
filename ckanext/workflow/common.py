# encoding: utf-8

# This file contains commonly used parts of external libraries. The idea is
# to help in removing helpers from being used as a dependency by many files
# but at the same time making it easy to change for example the json lib
# used.

import logging as _logging
import flask as _flask
getLogger = _logging.getLogger

from ckan import model as _model
import ckan.lib.plugins as _lib_plugins
import ckan.plugins as _plugins
from ckan.plugins import toolkit
import ckan.logic.auth as _logic_auth
import ckan.authz as _authz

users_role_for_group_or_org = _authz.users_role_for_group_or_org
has_user_permission_for_group_or_org = _authz.has_user_permission_for_group_or_org
# user_is_collaborator_on_dataset = _authz.user_is_collaborator_on_dataset
is_sysadmin = _authz.is_sysadmin

Blueprint = _flask.Blueprint

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

# full import of all toolkit attributes

# noinspection PyUnresolvedReferences
config = toolkit.config
# noinspection PyUnresolvedReferences,PyProtectedMember
ugettext = toolkit._
# noinspection PyUnresolvedReferences
ungettext = toolkit.ungettext
# noinspection PyUnresolvedReferences
c = toolkit.c
# noinspection PyUnresolvedReferences
g = toolkit.g
# noinspection PyUnresolvedReferences
h = toolkit.h
# noinspection PyUnresolvedReferences
request = toolkit.request
# noinspection PyUnresolvedReferences
render = toolkit.render
# noinspection PyUnresolvedReferences
abort = toolkit.abort
# noinspection PyUnresolvedReferences
asbool = toolkit.asbool
# noinspection PyUnresolvedReferences,SpellCheckingInspection
asint = toolkit.asint
# noinspection PyUnresolvedReferences,SpellCheckingInspection
aslist = toolkit.aslist
# noinspection PyUnresolvedReferences
literal = toolkit.literal
# noinspection PyUnresolvedReferences
get_action = toolkit.get_action
# noinspection PyUnresolvedReferences
chained_action = toolkit.chained_action
# noinspection PyUnresolvedReferences
get_converter = toolkit.get_converter
# noinspection PyUnresolvedReferences
get_validator = toolkit.get_validator
# noinspection PyUnresolvedReferences
check_access = toolkit.check_access
# noinspection PyUnresolvedReferences
chained_auth_function = toolkit.chained_auth_function
# noinspection PyUnresolvedReferences,SpellCheckingInspection
navl_validate = toolkit.navl_validate
# noinspection PyUnresolvedReferences
missing = toolkit.missing
# noinspection PyUnresolvedReferences
ObjectNotFound = toolkit.ObjectNotFound
# noinspection PyUnresolvedReferences
NotAuthorized = toolkit.NotAuthorized
# noinspection PyUnresolvedReferences
ValidationError = toolkit.ValidationError
# noinspection PyUnresolvedReferences
StopOnError = toolkit.StopOnError
# noinspection PyUnresolvedReferences
UnknownValidator = toolkit.UnknownValidator
# noinspection PyUnresolvedReferences
Invalid = toolkit.Invalid
# noinspection PyUnresolvedReferences
DefaultDatasetForm = toolkit.DefaultDatasetForm
# noinspection PyUnresolvedReferences
DefaultGroupForm = toolkit.DefaultGroupForm
# noinspection PyUnresolvedReferences
DefaultOrganizationForm = toolkit.DefaultOrganizationForm
# noinspection PyUnresolvedReferences
error_shout = toolkit.error_shout
# noinspection PyUnresolvedReferences
redirect_to = toolkit.redirect_to
# noinspection PyUnresolvedReferences
url_for = toolkit.url_for
# noinspection PyUnresolvedReferences
get_or_bust = toolkit.get_or_bust
# noinspection PyUnresolvedReferences
side_effect_free = toolkit.side_effect_free
# noinspection PyUnresolvedReferences
auth_sysadmins_check = toolkit.auth_sysadmins_check
# noinspection PyUnresolvedReferences
auth_allow_anonymous_access = toolkit.auth_allow_anonymous_access
# noinspection PyUnresolvedReferences
auth_disallow_anonymous_access = toolkit.auth_disallow_anonymous_access
# noinspection PyUnresolvedReferences
mail_recipient = toolkit.mail_recipient
# noinspection PyUnresolvedReferences
mail_user = toolkit.mail_user
# noinspection PyUnresolvedReferences
render_snippet = toolkit.render_snippet
# noinspection PyUnresolvedReferences
add_template_directory = toolkit.add_template_directory
# noinspection PyUnresolvedReferences
add_public_directory = toolkit.add_public_directory
# noinspection PyUnresolvedReferences
add_resource = toolkit.add_resource
# noinspection PyUnresolvedReferences
add_ckan_admin_tab = toolkit.add_ckan_admin_tab
# noinspection PyUnresolvedReferences
requires_ckan_version = toolkit.requires_ckan_version
# noinspection PyUnresolvedReferences
check_ckan_version = toolkit.check_ckan_version
# noinspection PyUnresolvedReferences
get_endpoint = toolkit.get_endpoint
# noinspection PyUnresolvedReferences
CkanVersionException = toolkit.CkanVersionException
# noinspection PyUnresolvedReferences
HelperError = toolkit.HelperError
# noinspection PyUnresolvedReferences
enqueue_job = toolkit.enqueue_job
# noinspection PyUnresolvedReferences
get_permissions = toolkit.get_permissions
# noinspection PyUnresolvedReferences
has_user_permission_for_organization = toolkit.has_user_permission_for_organization
# noinspection PyUnresolvedReferences
has_user_permission_for_group = toolkit.has_user_permission_for_group
# noinspection PyUnresolvedReferences
has_user_permission_for_package = toolkit.has_user_permission_for_package

### pylon imports
# # noinspection PyUnresolvedReferences
# response = toolkit.response
# # noinspection PyUnresolvedReferences
# BaseController = toolkit.BaseController
# # noinspection PyUnresolvedReferences
# CkanCommand = toolkit.CkanCommand
# # noinspection PyUnresolvedReferences
# load_config = toolkit.load_config


# converters/validators

convert_package_name_or_id_to_id = get_converter('convert_package_name_or_id_to_id')
empty_if_not_sysadmin = get_validator("empty_if_not_sysadmin")
ignore_missing = get_validator("ignore_missing")
unicode_safe = get_validator("unicode_safe")
ignore_not_sysadmin = get_validator("ignore_not_sysadmin")
boolean_validator = get_validator("boolean_validator")
isodate = get_validator("isodate")
ignore = get_validator("ignore")
empty = get_validator("empty")
one_of = get_validator("one_of")
convert_user_name_or_id_to_id = get_converter("convert_user_name_or_id_to_id")
not_empty = get_validator("not_empty")
not_missing = get_converter("not_missing")
ignore_empty = get_converter("ignore_empty")
configured_default = get_converter("configured_default")
limit_to_configured_maximum = get_converter("limit_to_configured_maximum")
natural_number_validator = get_validator("natural_number_validator")
