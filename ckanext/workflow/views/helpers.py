from ckan.plugins import toolkit
from ckan import model


def get_context():
    return {'model': model, 'session': model.Session, 'user': toolkit.c.user, 'auth_user_obj': toolkit.c.userobj}