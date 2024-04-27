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

def change(id, package_type):
    """
        Contains the logic for both publish and unpublish
    """
    context = utils.get_context(True)
    data_dict = dict(toolkit.request.values.to_dict(), id=id)
    try:
        toolkit.get_action("workflow_package_set_state")(context, data_dict)
        toolkit.h.flash_success("SDFGSDFGSDFGDSFGDFSG")
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
    return toolkit.redirect_to(u'{}.read'.format(package_type), id=id)



workflow.add_url_rule(
    rule=u'/change',
    view_func=change,
    methods=['POST']
)



def get_blueprints():
    return [workflow]
