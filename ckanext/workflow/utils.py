import ckanext.workflow.common as common
import logging
log = logging.getLogger(__name__)


def get_context(for_view=None):
    _context = {
        'model': common.model,
        'session': common.model.Session,
        'user': common.g.user,
        'for_view': True,
        'auth_user_obj': common.g.userobj
    }
    if for_view is not None:
        _context['for_view'] = for_view
    return _context
