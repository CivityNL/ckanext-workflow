'''API functions for getting data from CKAN.'''

from ckanext.workflow.model import WorkflowRequest
from ckan.plugins import toolkit

@toolkit.side_effect_free
def workflow_request_show(context, data_dict):
	### based on an ID, return the request
	request_id = toolkit.get_or_bust(data_dict, 'id')
	request = WorkflowRequest.get(request_id)
	if not request:
		raise toolkit.ObjectNotFound
	return request.as_dict()


@toolkit.side_effect_free
def workflow_request_list(context, data_dict):
	### based on query parameters, return the requests
	return [request.as_dict() for request in WorkflowRequest.all()]
