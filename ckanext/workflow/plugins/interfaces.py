# encoding: utf-8

u"""A collection of interfaces that CKAN plugins can implement to customize and
extend ckanext-workflow."""

from ckan.plugins.interfaces import Interface

# logging
import logging
log = logging.getLogger(__name__)


class IWorkflow(Interface):

    ####
    def get_default_state(self):
        pass

    # noinspection PyMethodMayBeStatic
    def get_states(self, states):
        return states

    # noinspection PyMethodMayBeStatic
    def get_transitions(self, transitions):
        return transitions

    # noinspection PyMethodMayBeStatic
    def get_update_actions(self, update_actions):
        return update_actions

    # noinspection PyMethodMayBeStatic
    def get_roles(self, roles):
        return roles


class IWorkflowRequestController(Interface):

    ####
    def before_request_create(self, context, request_dict):
        pass

    def after_request_create(self, context, request_dict):
        pass

    def before_request_update(self, context, request_dict):
        pass

    def after_request_update(self, context, request_dict):
        pass    

    def before_request_delete(self, context, request_dict):
        pass

    def after_request_delete(self, context, request_dict):
        pass  

    def before_request_purge(self, context, request_dict):
        pass

    def after_request_purge(self, context, request_dict):
        pass  


class IWorkflowPackageStateController(Interface):

    ####
    def before_package_state_update(self, context, pkg_dict):
        pass

    def after_package_state_update(self, context, pkg_dict):
        pass    
