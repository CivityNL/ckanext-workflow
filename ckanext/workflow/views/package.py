# encoding: utf-8

"""Provides NumberList and FrequencyDistribution, classes for statistics.

NumberList holds a sequence of numbers, and defines several statistical
operations (mean, stdev, etc.) FrequencyDistribution holds a mapping from
items (not necessarily numbers) to counts, and defines operations such as
Shannon entropy and frequency normalization.
"""

from flask import Blueprint
from ckan.plugins import toolkit
import ckanext.workflow.helpers as helpers
from ckanext.workflow.views.helpers import get_context
import ckanext.workflow.constants as workflow_constants
from plugins import PluginImplementations
from ckanext.workflow.plugins.interfaces import IWorkflowPackageStateController
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


def load_package(package_id):
    context = get_context()
    context['for_view'] = True

    try:
        extra_vars = {
            'pkg_dict': tk_get_action('package_show')(context, {'id': package_id}),
            'pkg': context['package'],
        }
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, tk__('Dataset not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(403, tk__('Unauthorized to read dataset %s') % package_id)
    for extra_var in extra_vars:
        setattr(toolkit.g, extra_var, extra_vars.get(extra_var))
    return extra_vars


def change(id, package_type):
    """
        Contains the logic for both publish and unpublish
    """
    context = get_context()
    data_dict = dict(tk_request.values.to_dict(), id=id)
    # noinspection PyProtectedMember
    from_state = helpers._get_state(id).label
    try:
        ### do state update
        result = toolkit.get_action('workflow_state_update')(dict(context, workflow_set_state=True), data_dict)
        #### finished

        to_state = helpers._get_state(result).label
        tk_h.flash_success(tk__('Successfully updated the state from {from_state} to {to_state}.').format(from_state=from_state, to_state=to_state))
    except tk_ObjectNotFound:
        # TRANSLATORS: TRANSLATORS: This is core translation, remove this from the generate pot file to prevent mishaps
        tk_abort(404, toolkit._('Dataset not found'))
    except tk_NotAuthorized as e:
        user = context.get('user')
        tk_h.flash_error(tk__('User {user} is not authorized to update the state from {from_state} for dataset {dataset}.').format(user=user, from_state=from_state, dataset=id))
    return tk_redirect_to(u'{}.read'.format(package_type), id=id)


def request(id, package_type):
    """
        Contains the logic for both publish and unpublish
    """
    context = get_context()
    pkg_dict = tk_get_action("package_show")(context, {"id": id})

    request = tk_request.values.to_dict()

    # noinspection PyProtectedMember
    data_dict = {
        "package_id": id,
        "state_id": helpers._get_state(id).id,
        "request_state": request.get("state"),
        "request_message": request.get("message", None)
    }
    # noinspection PyProtectedMember
    from_state = helpers._get_state(id).label
    try:
        pkg_dict = tk_get_action("workflow_request_create")(context, data_dict)
        # noinspection PyProtectedMember
        to_state = helpers._get_state(pkg_dict).label
        tk_h.flash_success(tk__('Successfully create a request for dataset {dataset}.').format(dataset=id))
    except tk_ObjectNotFound:
        # TRANSLATORS: TRANSLATORS: This is core translation, remove this from the generate pot file to prevent mishaps
        tk_abort(404, tk__('Dataset not found'))
    except tk_NotAuthorized as e:
        user = context.get('user')
        tk_h.flash_error(tk__('User {user} is not authorized to update the state from {from_state} for dataset {dataset}.').format(user=user, from_state=from_state, dataset=id))
    return tk_redirect_to(u'{}.read'.format(package_type), id=id)


def package_requests(id, package_type):
    return toolkit.render('package/workflow.html', extra_vars=load_package(id))


workflow_dataset = Blueprint(
    u"workflow_dataset",
    __name__,
    url_prefix=u'/dataset/<id>/workflow',
    url_defaults={u'package_type': u'dataset'}
)

workflow_dataset.add_url_rule(rule=u'/change', view_func=change, methods=['POST'])
workflow_dataset.add_url_rule(rule=u'/request', view_func=request, methods=['POST'])
workflow_dataset.add_url_rule(rule=u'/requests', view_func=package_requests, methods=['GET'])

