from ckan.plugins import toolkit
from ckanext.workflow.common import model
import logging
log = logging.getLogger(__name__)

_check_access = toolkit.check_access
_NotAuthorized = toolkit.NotAuthorized
_ValidationError = toolkit.ValidationError
_navl_validate = toolkit.navl_validate
_g = toolkit.g


def get_context(for_view = None):
    _context = {
        'model': model,
        'session': model.Session,
        'user': _g.user,
        'for_view': True,
        'auth_user_obj': _g.userobj
    }
    if for_view is not None:
        _context['for_view'] = for_view
    return _context
