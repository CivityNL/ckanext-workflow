import ckanext.workflow.common as common

log = common.getLogger(__name__)


def get_context():
    return {
        'model': common.model,
        'session': common.model.Session,
        'user': common.c.user,
        'auth_user_obj': common.c.userobj
    }
