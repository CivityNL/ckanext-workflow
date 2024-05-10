# encoding: utf-8

'''Model.'''

from __future__ import print_function
import sqlalchemy.orm as orm
import sqlalchemy.types as types
from ckan.model import meta, User, DomainObject
from ckanext.workflow.model.workflow_state import WorkflowState
import ckan.model.types as _types
import datetime

from sqlalchemy import Table, Column, ForeignKey, Index, CheckConstraint, ForeignKeyConstraint, UniqueConstraint
# logging
import logging

log = logging.getLogger(__name__)

mapper = orm.mapper

# list of states
REQUEST_STATE_PENDING = 'pending'
REQUEST_STATE_APPROVED = 'approved'
REQUEST_STATE_REJECTED = 'rejected'
REQUEST_STATE_DELETED = 'deleted'
REQUEST_STATE_RESOLVED = 'resolved'

# list of states meaning a request is still waiting for a reaction)
REQUEST_OPEN_STATES = [REQUEST_STATE_PENDING]
# list of states meaning a request is closed due to a reaction
REQUEST_HANDLED_STATES = [REQUEST_STATE_APPROVED, REQUEST_STATE_REJECTED]
# list of states meaning a request is closed because something which made the request invalid
REQUEST_IGNORED_STATES = [REQUEST_STATE_DELETED, REQUEST_STATE_RESOLVED]
REQUEST_STATES = REQUEST_OPEN_STATES + REQUEST_HANDLED_STATES + REQUEST_IGNORED_STATES


class WorkflowRequest(DomainObject):

    # list of all the columns to make them recognized by the IDE
    id = None
    package_id = None
    request_user_id = None
    request_state = None
    request_message = None
    request_timestamp = None
    process_user_id = None
    process_message = None
    process_timestamp = None
    process_state = None

    # list of all the relationships
    state = None
    requester = None

    @property
    def package(self):
        return self.state.package

    @classmethod
    def states(cls, open=None, handled=None, ignored=None):

        global REQUEST_OPEN_STATES, REQUEST_HANDLED_STATES, REQUEST_IGNORED_STATES

        result = REQUEST_OPEN_STATES + REQUEST_HANDLED_STATES + REQUEST_IGNORED_STATES

        if not all(option is None for option in [open, handled, ignored]):
            result = []
            if open:
                result += REQUEST_OPEN_STATES
            if handled:
                result += REQUEST_HANDLED_STATES
            if ignored:
                result += REQUEST_IGNORED_STATES

        return result


    def __init__(self, package_id, request_user_id, request_state, **kwargs):
        super(WorkflowRequest, self).__init__(**kwargs)
        self.id = _types.make_uuid()
        self.package_id = package_id
        self.request_user_id = request_user_id
        self.request_state = request_state

    @classmethod
    def all(cls):
        return meta.Session.query(cls).all()

    @classmethod
    def get(cls, id):
        return meta.Session.query(cls).filter(cls.id == id).one_or_none()

    @classmethod
    def get_for_package(cls, package_id):
        query = meta.Session.query(cls)
        query = query.filter(cls.state.package.has(id=package_id))
        return query.all()

    @classmethod
    def get_for_organization(cls, owner_org):
        query = meta.Session.query(cls)
        query = query.filter(cls.state.package.has(owner_org=owner_org))
        return query.all()

    @classmethod
    def get_for_user(cls, user_id, open, closed, approved, as_requester, as_approver):
        query = meta.Session.query(cls)
        if as_requester:
            query = query.filter(cls.requester_id == user_id)
        if as_approver:
            query = query.filter(cls.approver_id == user_id)
        if approved is not None:
            open = False
            query = query.filter(cls.approved == approved)

        all = True
        if open and not closed:
            query = query.filter(cls.approved.is_(None))
            all = False
        if closed and not open:
            query = query.filter(cls.approved.isnot_(None))

        result = []
        if all:
            result = query.all()
        else:
            result = query.one_or_none()
            result = [] if result is None else [result]

        return result


def define_workflow_request_table():

    workflow_request_table = Table(
        'workflow_request', meta.metadata,
        # generic identifier
        Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
        # Requester information
        Column('package_id', types.UnicodeText, ForeignKey('workflow_state.package_id', ondelete="CASCADE"), nullable=False),
        Column('request_user_id', types.UnicodeText, ForeignKey('user.id', ondelete="CASCADE"), nullable=False),
        Column('request_state', types.UnicodeText, nullable=False),
        # Additional request information
        Column('request_message', types.UnicodeText, default=None, nullable=True),
        Column('request_timestamp', types.DateTime, default=datetime.datetime.now(), nullable=False),
        # Approver information
        Column('process_user_id', types.UnicodeText, ForeignKey('user.id', ondelete="CASCADE"), default=None, nullable=True),
        Column('process_message', types.UnicodeText, default=None, nullable=True),
        Column('process_timestamp', types.DateTime, default=None, nullable=True),
        #
        Column('process_state', types.UnicodeText, default=REQUEST_STATE_PENDING, nullable=True)
    )
    Index(
        'workflow_request_only_one_active_request',
        workflow_request_table.c.package_id,
        workflow_request_table.c.request_state,
        workflow_request_table.c.process_state,
        unique=True,
        postgresql_where=workflow_request_table.c.process_state == REQUEST_STATE_PENDING
    )
    mapper(WorkflowRequest, workflow_request_table,
           properties={
               'state': orm.relationship(
                   WorkflowState, uselist=False,
                   backref=orm.backref(
                       'requests',
                       cascade='all, delete, delete-orphan'
                   )
               ),
               'requester': orm.relationship(User, primaryjoin=workflow_request_table.c.request_user_id == User.id,
                                             uselist=False),
           }, )
    return workflow_request_table
