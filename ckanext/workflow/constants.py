# encoding: utf-8

'''Constants.'''

from ckan.plugins import toolkit
# logging
import logging
log = logging.getLogger(__name__)

# noinspection PyProtectedMember
__ = toolkit._  # type: ignore

DEFAULT_STATE = 'draft'

DEFAULT_STATES = [
    {
        'id': 'draft',
        'label': lambda: __('Draft'),
        'dataset_fields': {
            'private': True,
            'contact_name': 'Henk'
        },
        'styling': {
            'text': '#123456',
            'background': '#123456'
        },
        'update_actions': [
            {'action': 'package_update', 'permission': 'read', 'to_state': 'draft'},
            # {'action': 'package_patch', 'permission': 'read', 'to_state': 'draft'},
            # {'action': 'package_relationship_create', 'permission': 'read', 'to_state': 'draft'},
        ]
    },
    {
        'id': 'private',
        'label': lambda: __('Private'),
        'dataset_fields': {
            'private': True
        },
        'styling': {
            'text': '#123456',
            'background': '#123456'
        },
        'update_actions': [
            {'action': 'package_update', 'permission': 'read', 'to_state': 'draft'},
            # {'action': 'package_patch', 'permission': 'read', 'to_state': 'draft'},
            # {'action': 'package_relationship_create', 'permission': 'read', 'to_state': 'draft'},
        ]
    },
    {
        'id': 'public',
        'label': lambda: __('Public'),
        'dataset_fields': {
            'private': False
        },
        'styling': {
            'text': '#123456',
            'background': '#123456'
        },
        'update_actions': [
            {'action': 'package_update', 'permission': 'read', 'to_state': 'draft'},
            # {'action': 'package_patch', 'permission': 'read', 'to_state': 'draft'},
            # {'action': 'package_relationship_create', 'permission': 'read', 'to_state': 'draft'},
        ]
    }
]

DEFAULT_TRANSITIONS = [
    {
        'from_state': 'draft',
        'to_state': 'private',
        'label': lambda: __('Review'),
        'styling': {
            'text': '#123456',
            'background': '#123456'
        },
        'can_assign': ["update_dataset"],
        'can_request': ["update_dataset"],
        'can_approve': ["update_dataset"],
        'request_message_required': True,
        'approve_message_required': True,
        'reject_message_required': True
    },
    {
        'from_state': 'private',
        'to_state': 'public',
        'label': lambda: __('Publish'),
        'styling': {
            'text': '#123456',
            'background': '#123456'
        },
        'can_assign': ["update_dataset"],
        'can_request': ["update_dataset"],
        'can_approve': ["update_dataset"],
        'request_message_required': False,
        'approve_message_required': False,
        'reject_message_required': True
    },
    {
        'from_state': 'public',
        'to_state': 'private',
        'label': lambda: __('Unpublish'),
        'styling': {
            'text': '#123456',
            'background': '#123456'
        },
        'can_assign': ["update_dataset"],
        'can_request': [],
        'can_approve': ["update_dataset"],
        'request_message_required': False,
        'approve_message_required': False,
        'reject_message_required': False
    }
]

DEFAULT_FIELD = 'workflowstatenewpleasework'

DEFAULT_UPDATE_ACTIONS = ["package_update"]
