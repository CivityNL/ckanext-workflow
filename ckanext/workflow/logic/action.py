from ckan.plugins import toolkit
from ckanext.workflow.model import WorkflowRequest
import ckanext.workflow.logic.schema as workflow_schema
import ckanext.workflow.constants as workflow_constants


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
	pass


def workflow_request_create(context, data_dict):
	###
    model = context["model"]
    session = context["session"]
    user = context["user"]
    schema = workflow_schema.workflow_request_create_schema()

    # fill 
    if 'requester_id' not in data_dict or not data_dict['request_id']:
         data_dict['request_id'] = user       

    data, errors = toolkit.navl_validate(data_dict, schema, context)
    if errors:
        session.rollback()
        raise toolkit.ValidationError(errors)

    request = WorkflowRequest.from_dict(data)

    request.save()
    return request.as_dict()
	


def workflow_request_update(context, data_dict):
	###
	pass


def workflow_request_delete(context, data_dict):
	###
	pass


def package_set_state(context, data_dict):
    id, state = toolkit.get_or_bust(data_dict, ['id', 'state'])
    toolkit.check_access('workflow_package_set_state', context, data_dict)

    _state = workflow_constants.WORKFLOW.get_state(state)
    package_patch_dict = {
         'id': id,
         workflow_constants.DEFAULT_FIELD: state,
         'extras': [{
              "key": workflow_constants.DEFAULT_FIELD,
              "value": state
         }]
    }
    if _state.dataset_fields:
        package_patch_dict.update(_state.dataset_fields)   
    toolkit.get_action('package_patch')(context, package_patch_dict)
