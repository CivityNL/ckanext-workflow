from ckan.plugins import toolkit


def package_publish(context, data_dict):
    return _action_publish_unpublish(context, data_dict, 'publish')


def package_unpublish(context, data_dict):
    return _action_publish_unpublish(context, data_dict, 'unpublish')


def _action_publish_unpublish(context, data_dict, action):
    """ actual implementation of the publish/unpublish action
        params: action : either 'package_publish' or 'package_unpublish'
    """
    toolkit.check_access("workflow_package_{}".format(action), context, data_dict)
    pkg_id = data_dict.get("id")
    private = False
    if action == 'unpublish':
        private = True
    return toolkit.get_action('package_patch')(context, {'id': pkg_id, 'private': private})
