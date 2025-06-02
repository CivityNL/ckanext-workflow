# encoding: utf-8

"""Provides NumberList and FrequencyDistribution, classes for statistics.

NumberList holds a sequence of numbers, and defines several statistical
operations (mean, stdev, etc.) FrequencyDistribution holds a mapping from
items (not necessarily numbers) to counts, and defines operations such as
Shannon entropy and frequency normalization.
"""

from ckanext.workflow.views.helpers import get_context
import ckanext.workflow.common as common
log = common.getLogger(__name__)


def load_organization(group_id):
    context = {
        'model': common.model,
        'session': common.model.Session,
        'user': common.g.user,
        'auth_user_obj': common.g.userobj
    }
    try:
        extra_vars = {
            'group_dict': common.get_action('organization_show')(context, {'id': group_id}),
            'group_type': 'organization'
        }
    except common.ObjectNotFound:
        return common.abort(404, common.ugettext('Organization not found'))
    except common.NotAuthorized:
        return common.abort(403, common.ugettext('Unauthorized to read organization %s') % group_id)
    for extra_var in extra_vars:
        setattr(common.g, extra_var, extra_vars.get(extra_var))
    return extra_vars


def organization_requests(id, group_type, is_organization):
    extra_vars = load_organization(id)
    extra_vars['requests'] = common.get_action("workflow_request_list")(get_context(), {'organization_id': id})
    return common.render('organization/workflow.html', extra_vars=extra_vars)


workflow_organization = common.Blueprint(
    u"workflow_organization",
    __name__,
    url_prefix=u'/organization/<id>/workflow',
    url_defaults={u'group_type': u'organization', u'is_organization': True}
)
workflow_organization.add_url_rule(rule=u'/requests', view_func=organization_requests, methods=['GET'])

