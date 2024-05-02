from ckan.plugins import toolkit
from ckanext.workflow.helpers import _get_state
from ckan.logic.auth import get_package_object

tk_chained_auth_function = toolkit.chained_auth_function
tk_auth_sysadmins_check = toolkit.auth_sysadmins_check
tk_get_or_bust = toolkit.get_or_bust

# noinspection PyProtectedMember
tk__ = toolkit._
tk_get_action = toolkit.get_action

