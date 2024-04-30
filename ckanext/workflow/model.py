# encoding: utf-8

'''Model.'''

from __future__ import print_function
import sqlalchemy.orm as orm
import sqlalchemy.types as types
import logging
import ckan.model as model
from ckan.model import meta, Group, User, Package, DomainObject
import ckan.model.types as _types
import datetime

from sqlalchemy import Table, Column, ForeignKey, Index, CheckConstraint, ForeignKeyConstraint, UniqueConstraint

mapper = orm.mapper
log = logging.getLogger(__name__)

workflow_request_table = None


# list of states
STATE_PENDING = 'pending'
STATE_APPROVED = 'approved'
STATE_REJECTED = 'rejected'
STATE_DELETED = 'deleted'
STATE_RESOLVED = 'resolved'

# list of states meaning a request is still waiting for a reaction)
OPEN_STATES = [STATE_PENDING]
# list of states meaning a request is closed due to a reaction
HANDLED_STATES = [STATE_APPROVED, STATE_REJECTED]
# list of states meaning a request is closed because something which made the request invalid
IGNORED_STATES = [STATE_DELETED, STATE_RESOLVED]
STATES = OPEN_STATES + HANDLED_STATES + IGNORED_STATES


def setup():
    if workflow_request_table is None:
        define_workflow_request_table()
        log.debug('Workflow table defined in memory')
    if not workflow_request_table.exists():
        workflow_request_table.create()
        log.debug('Workflow table created')


class WorkflowRequest(DomainObject):

    _package = None
    _organization = None
    _requester = None
    _processor = None

    @property
    def package(self):
        return self._package
    
    @property
    def organization(self):
        return self._organization

    @property
    def requester(self):
        return self._requester

    @property
    def processor(self):
        return self._processor

    def __init__(self, package_id, organization_id, state_id, request_user_id, request_state, request_message=None, request_timestamp=None, process_user_id=None, process_message=None, process_timestamp=None, process_state=None):
        self.id = id
        self.package_id = package_id
        self.organization_id = organization_id
        self.state_id = state_id
        self.request_user_id = request_user_id
        self.request_state = request_state
        self.request_message = request_message
        self.request_timestamp = request_timestamp
        self.process_user_id = process_user_id
        self.process_message = process_message
        self.process_timestamp = process_timestamp
        self.process_state = process_state 
                                
        self.id = _types.make_uuid()
        self.request_timestamp = request_timestamp if request_timestamp is not None else datetime.datetime.now()
        self.process_state = process_state if process_state is not None else STATE_PENDING

    @classmethod
    def all(cls):
        return meta.Session.query(cls).all()    

    @classmethod
    def get(cls, id):
        return meta.Session.query(cls).filter(cls.id == id).one_or_none()

    @classmethod
    def get_for_package(cls, package_id, open, closed, approved):
        query = meta.Session.query(cls)

        query = meta.Session.query(cls)
        query = query.filter(cls.package_id == package_id)
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
                
        return query.first()
    
    @classmethod
    def get_for_organization(cls, organization_id, open, closed, approved):
        query = meta.Session.query(cls)
        query = query.filter_by(organization_id=organization_id)
        return query.first()
    
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

    def as_dict(self):
        dict = super(WorkflowRequest, self).as_dict()
        for attr in ["package", "organization", "requester", "processer"]:
            value = getattr(self, attr, None)
            if value is not None:
                dict[attr] = value.as_dict()
        return dict


def define_workflow_request_table():
    global workflow_request_table

    def get_foreign_key(column: str):
        return ForeignKey(column, onupdate="CASCADE", ondelete="CASCADE")

    workflow_request_table = Table(
        'workflow_request', meta.metadata,
        Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
        # Package/Organization information (package_id/state_id + owner_org)
        Column('package_id', types.UnicodeText, get_foreign_key('package.id'), nullable=False),
        Column('organization_id', types.UnicodeText, get_foreign_key('group.id'), nullable=False),
        Column('state_id', types.UnicodeText, nullable=False),

        # Requester information 
        Column('request_user_id', types.UnicodeText, get_foreign_key('user.id'), nullable=False),
        Column('request_state', types.UnicodeText, nullable=False),
        Column('request_message', types.UnicodeText, default=None, nullable=True),
        Column('request_timestamp', types.DateTime, default=datetime.datetime.now(), nullable=False),
        # Approver information
        Column('process_user_id', types.UnicodeText, get_foreign_key('user.id'), default=None, nullable=True),
        Column('process_message', types.UnicodeText, default=None, nullable=True),
        Column('process_timestamp', types.DateTime, default=None, nullable=True),
        # 
        Column('process_state', types.UnicodeText, default=STATE_PENDING, nullable=True)
    )
    Index(
        'workflow_request_only_one_active_request', 
        workflow_request_table.c.package_id, workflow_request_table.c.request_user_id, workflow_request_table.c.request_state, workflow_request_table.c.process_state,
        unique=True, 
        postgresql_where=workflow_request_table.c.process_state == STATE_PENDING
    )
    mapper(WorkflowRequest, workflow_request_table,
           properties={
            '_package': orm.relationship(Package, uselist=False),
            '_organization': orm.relationship(Group, uselist=False),
            '_requester': orm.relationship(User, primaryjoin=workflow_request_table.c.request_user_id == User.id, uselist=False),
            '_processor': orm.relationship(User, primaryjoin=workflow_request_table.c.process_user_id == User.id, uselist=False)
        },)
