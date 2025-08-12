# encoding: utf-8

"""Provides NumberList and FrequencyDistribution, classes for statistics.

NumberList holds a sequence of numbers, and defines several statistical
operations (mean, stdev, etc.) FrequencyDistribution holds a mapping from
items (not necessarily numbers) to counts, and defines operations such as
Shannon entropy and frequency normalization.
"""

import ckanext.workflow.helpers as helpers
from ckanext.workflow.views.helpers import get_context
import ckanext.workflow.common as common
from ckanext.workflow.model import WorkflowRequest
log = common.getLogger(__name__)

from collections import OrderedDict




def load_package(package_id):
    context = get_context()
    context['for_view'] = True

    try:
        extra_vars = {
            'pkg_dict': common.get_action('package_show')(context, {'id': package_id}),
            'pkg': context['package'],
        }
    except common.ObjectNotFound:
        return common.abort(404, common.ugettext('Dataset not found'))
    except common.NotAuthorized:
        return common.abort(403, common.ugettext('Unauthorized to read dataset %s') % package_id)
    for extra_var in extra_vars:
        setattr(common.g, extra_var, extra_vars.get(extra_var))
    return extra_vars


def change(id, package_type):
    """
        Contains the logic for both publish and unpublish
    """
    context = get_context()
    data_dict = dict(common.request.values.to_dict(), package_id=id)
    from_state = helpers.get_state_label(id)
    try:
        ### do state update
        common.get_action('workflow_state_update')(dict(context, workflow_set_state=True), data_dict)
        #### finished
        to_state = helpers.get_state_label(id)
        common.h.flash_success(common.ugettext('Successfully updated the state from {from_state} to {to_state}.').format(from_state=from_state, to_state=to_state))
    except common.ObjectNotFound:
        # TRANSLATORS: TRANSLATORS: This is core translation, remove this from the generate pot file to prevent mishaps
        common.abort(404, common.ugettext('Dataset not found'))
    except common.NotAuthorized as e:
        user = context.get('user')
        common.h.flash_error(common.ugettext('User {user} is not authorized to update the state from {from_state} for dataset {dataset}.').format(user=user, from_state=from_state, dataset=id))
    return common.redirect_to(u'{}.read'.format(package_type), id=id)


def request(id, package_type):
    """
        Contains the logic for both publish and unpublish
    """
    context = get_context()
    pkg_dict = common.get_action("package_show")(context, {"id": id})

    request = common.request.values.to_dict()

    # noinspection PyProtectedMember
    data_dict = {
        "package_id": id,
        "state_id": helpers._get_state_id(id),
        "request_user_id": request.get("request_user_id", common.g.userobj.id),
        "request_state": request.get("state_id"),
        "request_message": request.get("request_message", None)
    }
    # noinspection PyProtectedMember
    from_state = helpers.get_state_label(id)
    try:
        request_dict = common.get_action("workflow_dataset_request_create")(context, data_dict)
        # noinspection PyProtectedMember
        to_state = helpers.get_state_label(request_dict.get('package_id'))
        common.h.flash_success(
            common.ugettext('Successfully create a request to state {to_state} for dataset {dataset}.').format(dataset=id, to_state=to_state))
    except common.ObjectNotFound:
        # TRANSLATORS: TRANSLATORS: This is core translation, remove this from the generate pot file to prevent mishaps
        common.abort(404, common.ugettext('Dataset not found'))
    except common.NotAuthorized as e:
        user = context.get('user')
        common.h.flash_error(common.ugettext('User {user} is not authorized to update the state from {from_state} for dataset {dataset}.').format(user=user, from_state=from_state, dataset=id))
    return common.redirect_to(u'{}.read'.format(package_type), id=id)


def request_show(id, package_type, request_id):
    extra_vars = load_package(id)

    extended = 'extended' in common.request.values

    activities = common.get_action("workflow_request_activity_list")(get_context(), {'id': request_id})
    messages = common.get_action("workflow_request_message_list")(get_context(), {'id': request_id})
    actors = dict()

    _dict = {(activity.get("timestamp"), 'activity'): activity for activity in activities}
    _dict.update({(message.get("created"), 'message'): message for message in messages})

    if extended:
        print(f"extended = {extended}")
        stream = OrderedDict(sorted(_dict.items()))
    else:
        print(f"extended = {extended}")
        stream = OrderedDict()
        prev = None
        for key, item in sorted(_dict.items()):
            print(f"item = {item}")
            timestamp, type = key
            if type == 'message':
                stream[key] = [item]
                prev = None
            elif prev is None:
                stream[key] = [item]
                prev = key
            elif common.h.time_ago_from_timestamp(prev[0]) == common.h.time_ago_from_timestamp(timestamp):
                # add to prev key
                stream[prev].append(item)
            else:
                # something new
                stream[key] = [item]
                prev = key
        for activity_key in [key for key in stream.keys() if key[1] == 'activity']:
            activity_users = [a.get('user_id') for a in stream[activity_key]]
            actors[activity_key] = sorted(set(activity_users), key=lambda u: -activity_users.count(u))

    print(f"stream = {stream}")
    print(f"actors = {actors}")

    extra_vars['workflow_request'] = common.get_action("workflow_dataset_request_show")(get_context(), {'id': request_id})
    extra_vars['stream'] = stream
    extra_vars['actors'] = actors

    return common.render('package/workflow_request.html', extra_vars=extra_vars)


def add_message(id, package_type, request_id):
    print(f"add_message(id, package_type, request_id)")
    pass


def change_message(id, package_type, request_id, message_id):
    print(f"change_message(id, package_type, request_id, message_id)")
    pass


def delete_message(id, package_type, request_id, message_id):
    print(f"delete_message(id, package_type, request_id, message_id)")
    pass


def package_requests(id, package_type):
    extra_vars = load_package(id)
    #
    extra_vars['requests'] = WorkflowRequest.all()
    # extra_vars['requests'] = common.get_action("workflow_dataset_request_list")(get_context(), {'package_id': id})
    return common.render('package/workflow.html', extra_vars=extra_vars)


workflow_dataset = common.Blueprint(
    u"workflow_dataset",
    __name__,
    url_prefix=u'/dataset/<id>/workflow',
    url_defaults={u'package_type': u'dataset'}
)

workflow_dataset.add_url_rule(rule=u'/change', view_func=change, methods=['POST'])
workflow_dataset.add_url_rule(rule=u'/request', view_func=request, methods=['POST'])
workflow_dataset.add_url_rule(rule=u'/request/<request_id>', view_func=request_show, methods=['GET'])
workflow_dataset.add_url_rule(rule=u'/request/<request_id>/message', view_func=add_message, methods=['POST'])
workflow_dataset.add_url_rule(rule=u'/request/<request_id>/message/<message_id>', view_func=change_message, methods=['POST', 'PATCH'])
workflow_dataset.add_url_rule(rule=u'/request/<request_id>/message/<message_id>', view_func=delete_message, methods=['DELETE'])
workflow_dataset.add_url_rule(rule=u'/requests', view_func=package_requests, methods=['GET'])
