'''
Created on July 2nd, 2015

@author: dan
'''
from __future__ import print_function
import sqlalchemy.orm as orm
import sqlalchemy.types as types
import logging
import ckan.model as model
from ckan.model import meta, Group, User, Package, DomainObject
import ckan.model.types as _types
import datetime

from sqlalchemy import Table, Column, ForeignKey, Index, CheckConstraint, ForeignKeyConstraint

mapper = orm.mapper
log = logging.getLogger(__name__)

workflow_request_table = None

REQUESTS = ['publish', 'review']


def setup():
    if workflow_request_table is None:
        define_workflow_request_table()
        log.debug('Workflow table defined in memory')

    create_table()


class WorkflowRequest(DomainObject):

    id = None
    package_id = None
    organization_id = None
    requester_id = None
    request_message = None
    request_timestamp = None
    approver_id = None
    approve_message = None
    approve_timestamp = None
    approved = None

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
    def approver(self):
        return self._approver

    def __init__(self, package_id, organization_id, requester_id, request_message = None, request_timestamp = None):
        self.id = _types.make_uuid()
        self.package_id = package_id
        self.organization_id = organization_id
        self.requester_id = requester_id
        self.request_message = request_message
        self.request_timestamp = request_timestamp if request_timestamp is not None else datetime.datetime.now()

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


def define_workflow_request_table():
    global workflow_request_table
    fk_on = {
        "onupdate": 'CASCADE',
        "ondelete": 'CASCADE'
    }
    workflow_request_table = Table(
        'workflow_request', meta.metadata,
        Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
        # Package/Organization information (package_id + owner_org)
        Column('package_id', types.UnicodeText, ForeignKey('package.id', **fk_on), nullable=False),
        Column('organization_id', types.UnicodeText, ForeignKey('group.id', **fk_on), nullable=False),
        # some current state ???
        # Requester information 
        Column('requester_id', types.UnicodeText, ForeignKey('user.id', **fk_on), nullable=False),
        Column('request_state', types.UnicodeText, nullable=False),
        Column('request_message', types.UnicodeText, default=None, nullable=True),
        Column('request_timestamp', types.DateTime, default=datetime.datetime.now(), nullable=False),
        # Approver information
        Column('approver_id', types.UnicodeText, ForeignKey('user.id', **fk_on), default=None, nullable=True),
        Column('approve_message', types.UnicodeText, default=None, nullable=True),
        Column('approve_timestamp', types.DateTime, default=None, nullable=True),
        # 
        Column('approved', types.Boolean, default=None, nullable=True),
    )
    Index(
        'only_one_active_request', 
        workflow_request_table.c.package_id, workflow_request_table.c.approved, 
        unique=True, 
        postgresql_where=workflow_request_table.c.approved.is_(None)
    )
    mapper(WorkflowRequest, workflow_request_table,
           properties={
            '_package': orm.relationship(Package, uselist=False),
            '_organization': orm.relationship(Group, uselist=False),
            '_requester': orm.relationship(User, primaryjoin=workflow_request_table.c.requester_id == User.id, uselist=False),
            '_approver': orm.relationship(User, primaryjoin=workflow_request_table.c.approver_id == User.id, uselist=False)
        },)


def create_table():
    '''
    Create user_extra table
    '''
    if not workflow_request_table.exists():
        workflow_request_table.create()
        log.debug('Workflow table created')
