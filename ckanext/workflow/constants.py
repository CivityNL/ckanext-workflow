# encoding: utf-8

'''Constants.'''

from ckanext.workflow.backend import Workflow
from ckan.authz import ROLE_PERMISSIONS
from ckan.plugins import toolkit
# logging
import logging
log = logging.getLogger(__name__)

# noinspection PyProtectedMember
__ = toolkit._  # type: ignore

CAPACITIES = []
PERMISSIONS = []
PERMISSION_PREFIX = "permission-"

DEFAULT_ROLES = ROLE_PERMISSIONS

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
        'can_update': ["editor", "admin"],
        'on_update': "draft",
        'update_actions': [
            {'action': 'package_update'},
            {'action': 'package_patch'},
            {'action': 'package_relationship_create'}
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
        'can_update': ["editor", "admin"],
        'on_update': "draft",
        'update_actions': [
            {'action': 'package_update'},
            {'action': 'package_patch'},
            {'action': 'package_relationship_create'}
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
        'can_update': [],
        'on_update': 'private',
        'update_actions': [
            {'action': 'package_update'},
            {'action': 'package_patch'},
            {'action': 'package_relationship_create'}
        ]
    }
]

DEFAULT_TRANSITIONS = [
    {
        'from_state': 'draft',
        'to_state': 'private',
        'label': lambda: __('Review'),
        'request_required': False,
        'styling': {
            'text': '#123456',
            'background': '#123456'
        },
        'can_request': ["member", "permission-read"],
        'can_approve': ["editor", "admin"],
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
        'request_required': False,
        'can_request': ["editor"],
        'can_approve': ["admin"],
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
        'request_required': False,
        'can_request': [],
        'can_approve': ["editor", "admin"],
        'request_message_required': False,
        'approve_message_required': False,
        'reject_message_required': False
    }
]

WORKFLOW: Workflow

DEFAULT_FIELD = 'workflowstatenewpleasework'

DEFAULT_UPDATE_ACTIONS = ["resource_create", "resource_update", "resource_patch", "resource_delete",
                          "package_update", "package_revise", "package_patch"]
