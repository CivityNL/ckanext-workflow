from ckan.plugins import toolkit
from ckan import model


def get_context(for_view: bool = None):
    _context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.g.user,
        'for_view': True,
        'auth_user_obj': toolkit.g.userobj
    }
    if for_view is not None:
        _context['for_view'] = for_view
    return _context


def check_access(action, context, data_dict):
    """ Wrapper around the toolkit.check_access which will return False instead of a NotAuthorized """
    result = False
    try:
        result = toolkit.check_access(action, context, data_dict)
    except toolkit.NotAuthorized:
        pass
    return result


def show(pkg_dict, should_pkg_be_private, action, should_action_be_allowed, context=None):
    if context is None:
        context = get_context()
    return pkg_dict.get("private") == should_pkg_be_private and check_access(action, context, pkg_dict) == should_action_be_allowed
