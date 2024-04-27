from ckanext.workflow.logic.interface import Workflow
from ckan.authz import ROLE_PERMISSIONS
from ckan.plugins import toolkit

CAPACITIES = []
PERMISSIONS = []
PERMISSION_PREFIX = "permission-"

DEFAULT_ROLES = ROLE_PERMISSIONS

DEFAULT_STATE = 'draft'

DEFAULT_STATES = [
            {
                'id': 'draft',
                'label': lambda: toolkit._('Draft'),
                'dataset_fields': {
                    'private': True
                },
                'can_update': ["editor", "admin"],
                'on_update': ["draft"],
                'update_events': [
                    {'action': 'package_update'},
                    {'action': 'package_patch'},
                    {'action': 'package_relationship_create'}
                ]
            },
            {
                'id': 'private',
                'label': lambda: toolkit._('Private'),
                'dataset_fields': {
                    'private': True
                },
                'can_update': ["editor", "admin"],
                'on_update': ["draft"],
                'update_events': [
                    {'action': 'package_update'},
                    {'action': 'package_patch'},
                    {'action': 'package_relationship_create'}
                ]
            },
            {
                'id': 'public',
                'label': lambda: toolkit._('Public'),
                'dataset_fields': {
                    'private': False
                },
                'can_update': [],
                'on_update': None,
                'update_events': [
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
        'label': lambda : toolkit._('Review'),
        'request_required': False,
	    'can_request': ["member", "permission-read"],
	    'can_approve': ["editor", "admin"],
	    'request_message_required': True,
	    'approve_message_required': True,
	    'reject_message_required': True
    },
    {
        'from_state': 'private',
        'to_state': 'public',
        'label': lambda : toolkit._('Publish'),
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
        'label': lambda : toolkit._('Unpublish'),
        'request_required': False,
	    'can_request': [],
	    'can_approve': ["editor", "admin"],
	    'request_message_required': False,
	    'approve_message_required': False,
	    'reject_message_required': False
    }
]

WORKFLOW: Workflow = None

DEFAULT_FIELD = 'workflow_state'