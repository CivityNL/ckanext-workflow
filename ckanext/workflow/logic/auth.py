'''API functions for creating data from CKAN.'''

import ckanext.workflow.common as common

side_effect_free = common.side_effect_free
log = common.getLogger(__name__)

from ckanext.workflow.logic import DEFAULT_ACTIONS, OBJECT_TYPES

__all__ = [f'workflow_{o}_{a}' for a in DEFAULT_ACTIONS for o in OBJECT_TYPES]


def workflow_state_create(context, validated_data_dict):
    log.warning("AUTH workflow_state_create still needs to be implemented")
    return {'success': True}

def workflow_state_update(context, validated_data_dict):
    log.warning("AUTH workflow_state_update still needs to be implemented")
    return {'success': True}

def workflow_state_patch(context, validated_data_dict):
    log.warning("AUTH workflow_state_patch still needs to be implemented")
    return {'success': True}

def workflow_state_delete(context, validated_data_dict):
    log.warning("AUTH workflow_state_delete still needs to be implemented")
    return {'success': True}

def workflow_state_purge(context, validated_data_dict):
    log.warning("AUTH workflow_state_purge still needs to be implemented")
    return {'success': True}

def workflow_state_show(context, validated_data_dict):
    log.warning("AUTH workflow_state_show still needs to be implemented")
    return {'success': True}

def workflow_state_list(context, validated_data_dict):
    log.warning("AUTH workflow_state_list still needs to be implemented")
    return {'success': True}



def workflow_request_create(context, data_dict):
    log.warning("AUTH workflow_request_create still needs to be implemented")
    return {'success': True}

def workflow_request_update(context, data_dict):
    log.warning("AUTH workflow_request_update still needs to be implemented")
    return {'success': True}

def workflow_request_patch(context, data_dict):
    log.warning("AUTH workflow_request_patch still needs to be implemented")
    return {'success': True}

def workflow_request_delete(context, data_dict):
    log.warning("AUTH workflow_request_delete still needs to be implemented")
    return {'success': True}

def workflow_request_purge(context, data_dict):
    log.warning("AUTH workflow_request_purge still needs to be implemented")
    return {'success': True}

def workflow_request_show(context, data_dict):
    log.warning("AUTH workflow_request_show still needs to be implemented")
    return {'success': True}

def workflow_request_list(context, data_dict):
    log.warning("AUTH workflow_request_list still needs to be implemented")
    return {'success': True}



def workflow_message_create(context, data_dict):
    log.warning("AUTH workflow_message_create still needs to be implemented")
    return {'success': True}

def workflow_message_update(context, data_dict):
    log.warning("AUTH workflow_message_update still needs to be implemented")
    return {'success': True}

def workflow_message_patch(context, data_dict):
    log.warning("AUTH workflow_message_patch still needs to be implemented")
    return {'success': True}

def workflow_message_delete(context, data_dict):
    log.warning("AUTH workflow_message_delete still needs to be implemented")
    return {'success': True}

def workflow_message_purge(context, data_dict):
    log.warning("AUTH workflow_message_purge still needs to be implemented")
    return {'success': True}

def workflow_message_show(context, data_dict):
    log.warning("AUTH workflow_message_show still needs to be implemented")
    return {'success': True}

def workflow_message_list(context, data_dict):
    log.warning("AUTH workflow_message_list still needs to be implemented")
    return {'success': True}
