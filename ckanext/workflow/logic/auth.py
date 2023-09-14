from ckanext.workflow import utils
from ckan.plugins import toolkit

_ = toolkit._


def package_publish(context, data_dict):
    """ authorization check for package_publish based on package_update and
        if the user is allowed to publish """
    package_update_permission = utils.check_access('package_update', context, data_dict)
    if not has_publish_permission(context, data_dict) or not package_update_permission:
        user = context.get('user')
        package_id = data_dict.get("id")
        msg = _('User {user} not authorized to publish dataset {package}'.format(user=user, package=package_id))
        return {'success': False, 'msg': msg}
    return {'success': True}


def package_unpublish(context, data_dict):
    """ authorization check for package_unpublish based on package_update """
    if not utils.check_access('package_update', context, data_dict):
        user = context.get('user')
        package_id = data_dict.get("id")
        msg = _('User {user} not authorized to unpublish dataset {package}'.format(user=user, package=package_id))
        return {'success': False, 'msg': msg}
    return {'success': True}


def has_publish_permission(context, data_dict):
    """ check if user is allowed to publish
        params: user: name or id,
                org : name or id
    """

    roles = ["admin"]

    user = context.get("user", None)
    if user is None:
        return False

    pkg_dict = toolkit.get_action("package_show")(context, data_dict)
    owner_org = pkg_dict.get("owner_org")
    if owner_org is None:
        return False

    member_roles_list = toolkit.get_action("member_roles_list")(context, {"group_type": "organization"})
    member_list = toolkit.get_action("member_list")(context, {"id": owner_org, "object_type": "user"})
    user_id = toolkit.get_converter('convert_user_name_or_id_to_id')(context.get("user"), context)
    if user_id is None:
        return False

    member_dict = {_id: role for (_id, _, role) in member_list}
    trans_role = member_dict.get(user_id, None)
    if trans_role is None:
        return False

    member_roles_dict = {role.get("text"): role.get("value") for role in member_roles_list}
    role = member_roles_dict.get(trans_role, None)
    if role is None or role not in roles:
        return False

    return True
