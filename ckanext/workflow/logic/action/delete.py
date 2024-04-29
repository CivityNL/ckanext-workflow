'''API functions for deleting data from CKAN.'''


from ckanext.workflow.plugin.interface import IWorkflowRequestController
from ckan.plugins import PluginImplementations


def workflow_request_delete(context, data_dict):
    plugin: IWorkflowRequestController
    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.before_request_delete(context, data_dict)
    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.after_request_delete(context, data_dict)


def workflow_request_purge(context, data_dict):
    plugin: IWorkflowRequestController
    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.before_request_purge(context, data_dict)
    for plugin in PluginImplementations(IWorkflowRequestController):
         plugin.after_request_purge(context, data_dict)
