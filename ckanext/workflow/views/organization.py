# encoding: utf-8

"""Provides NumberList and FrequencyDistribution, classes for statistics.

NumberList holds a sequence of numbers, and defines several statistical
operations (mean, stdev, etc.) FrequencyDistribution holds a mapping from
items (not necessarily numbers) to counts, and defines operations such as
Shannon entropy and frequency normalization.
"""

from flask import Blueprint
from ckan.plugins import toolkit
from ckanext.workflow.views.helpers import get_context
# logging
import logging
log = logging.getLogger(__name__)

# noinspection PyProtectedMember
tk__ = toolkit._
tk_request = toolkit.request
tk_get_action = toolkit.get_action
tk_abort = toolkit.abort
tk_ObjectNotFound = toolkit.ObjectNotFound
tk_NotAuthorized = toolkit.NotAuthorized
tk_h = toolkit.h
tk_redirect_to = toolkit.redirect_to


def load_organization(group_id):
    context = get_context()
    extra_vars = {}

    try:
        extra_vars = {
            'group_dict': tk_get_action('organization_show')(context, {'id': group_id}),
            'group_type': 'organization'
        }
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, tk__('Organization not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(403, tk__('Unauthorized to read organization %s') % group_id)
    for extra_var in extra_vars:
        setattr(toolkit.g, extra_var, extra_vars.get(extra_var))
    return extra_vars


def organization_requests(id, group_type, is_organization):
    return toolkit.render('organization/workflow.html', extra_vars=load_organization(id))


workflow_organization = Blueprint(
    u"workflow_organization",
    __name__,
    url_prefix=u'/organization/<id>/workflow',
    url_defaults={u'group_type': u'organization', u'is_organization': True}
)
workflow_organization.add_url_rule(rule=u'/requests', view_func=organization_requests, methods=['GET'])

