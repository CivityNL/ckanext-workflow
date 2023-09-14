from flask import Blueprint
from ckanext.workflow import utils
from ckan.plugins import toolkit

_ = toolkit._


workflow = Blueprint(
    u"workflow",
    __name__,
    url_prefix=u'/dataset/<id>',
    url_defaults={u'package_type': u'dataset'}
)


def do_publish(package_id, package_type, action):
    """
        Contains the logic for both publish and unpublish
    """
    context = utils.get_context(True)
    data_dict = {'id': package_id}

    try:
        toolkit.get_action("workflow_package_{}".format(action))(context, data_dict)
    except toolkit.ObjectNotFound:
        # TRANSLATORS: TRANSLATORS: This is core translation, remove this from the generate pot file to prevent mishaps
        toolkit.abort(404, _('Dataset not found'))
    except toolkit.NotAuthorized:
        user = context.get('user')
        msg = None
        if action == 'publish':
            msg = _('User {user} not authorized to unpublish dataset {package}'.format(user=str(user), package=package_id))
        if action == 'unpublish':
            msg = _('User {user} not authorized to unpublish dataset {package}'.format(user=str(user), package=package_id))
        toolkit.abort(403, msg)
    return toolkit.redirect_to(u'{}.read'.format(package_type), id=package_id)


def publish(id, package_type):
    return do_publish(id, package_type, 'publish')


def unpublish(id, package_type):
    return do_publish(id, package_type, 'unpublish')


workflow.add_url_rule(
    rule=u'/publish',
    view_func=publish
)
workflow.add_url_rule(
    rule=u'/unpublish',
    view_func=unpublish
)


def get_blueprints():
    return [workflow]
