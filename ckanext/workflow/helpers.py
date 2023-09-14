from ckanext.workflow import utils


def show_publish_button(pkg_dict):
    return utils.show(pkg_dict, True, 'workflow_package_publish', True)


def show_unpublish_button(pkg_dict):
    return utils.show(pkg_dict, False, 'workflow_package_unpublish', True)


def show_notice_to_be_unpublished_on_edit(pkg_dict):
    return utils.show(pkg_dict, False, 'workflow_package_publish', False)
