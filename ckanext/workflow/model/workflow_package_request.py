# encoding: utf-8

'''Model.'''

from __future__ import print_function
import sqlalchemy.orm as orm
import sqlalchemy.types as types
from ckan.model import meta, User, DomainObject
import ckan.model as model
from ckanext.workflow.model.workflow_package_state import WorkflowPackageState
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


class WorkflowPackageRequest(DomainObject):
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
    modified_timestamp = None

    # list of all the relationships
    _state = None
    _requester = None

    @property
    def state(self):
        return self._state

    @property
    def requester(self):
        return self._requester

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
        super(WorkflowPackageRequest, self).__init__(**kwargs)
        self.id = _types.make_uuid()
        self.package_id = package_id
        self.request_user_id = request_user_id
        self.request_state = request_state

    @classmethod
    def all(cls):
        return model.Session.query(cls).all()

    @classmethod
    def get(cls, id):
        return model.Session.query(cls).filter(cls.id == id).one_or_none()

    @classmethod
    def query_for_package(cls, package_id):
        query = model.Session.query(cls)
        query = query.filter_by(package_id=package_id)
        return query

    @classmethod
    def get_for_package(cls, package_id):
        return cls.query_for_package(package_id).all()

    @classmethod
    def count_for_package(cls, package_id):
        return cls.query_for_package(package_id).count()

    @classmethod
    def get_for_organization(cls, owner_org):
        query = model.Session.query(cls)
        query = query.filter(cls.state.package.has(owner_org=owner_org))
        return query.all()

    def set_process(self, process_state, process_user_id, process_message=None, process_timestamp=None):
        self.process_state = process_state
        self.process_user_id = process_user_id
        self.process_timestamp = datetime.datetime.utcnow() if process_timestamp is None else process_timestamp
        self.process_message = process_message

    def set_resolved(self, user_id, process_message=None):
        self.set_process(REQUEST_STATE_RESOLVED, user_id, process_message)

    def set_deleted(self, user_id, process_message=None):
        self.set_process(REQUEST_STATE_DELETED, user_id, process_message)

    def save_activity(self, context, activity_type='updated'):
        model = context["model"]
        session = context["session"]
        actor = model.User.by_name(context["user"])
        activity = model.Activity(
            actor.id, self.id, "{} request".format(activity_type),
            {'request': self.as_dict(), 'actor': actor.name}
        )
        print("adding new Activity to session")
        session.add(activity)

    def save_context(self, context, add_activity=True, activity_type='updated'):
        model = context["model"]
        session = context["session"]
        print("adding new WorkflowPackageRequest to session")
        session.add(self)
        if add_activity:
            self.save_activity(context, activity_type)
        if not context.get('defer_commit'):
            session.commit()
        return self

    @classmethod
    def create(cls, context, data_dict, add_activity=True):
        workflow_package_request = cls(**data_dict)
        return workflow_package_request.save_context(context, add_activity, 'new')

    def changes(self, data_dict):
        return [key for key in data_dict if getattr(self, key) != data_dict[key]]

    @classmethod
    def update(cls, context, data_dict, add_activity=True, activity_type='updated'):
        workflow_package_request = cls.get(data_dict["id"])
        changes = workflow_package_request.changes(data_dict)
        print(f"update {workflow_package_request} {changes}")
        if changes:
            for key in data_dict:
                setattr(workflow_package_request, key, data_dict[key])
            workflow_package_request.modified_timestamp = datetime.datetime.utcnow()
            if ("process_state" in changes and workflow_package_request.process_state not in REQUEST_OPEN_STATES and
                    not workflow_package_request.process_timestamp):
                workflow_package_request.process_timestamp = datetime.datetime.utcnow()
            workflow_package_request.save_context(context, add_activity, activity_type)
        return workflow_package_request

    @classmethod
    def get_for_user(cls, user_id, open, closed, approved, as_requester, as_approver):
        query = model.Session.query(cls)
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


def define_workflow_package_request_table():
    workflow_package_request_table = Table(
        'workflow_package_request', meta.metadata,
        # generic identifier
        Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
        Column('modified_timestamp', types.DateTime, default=datetime.datetime.now(), nullable=False),
        Column('package_id', types.UnicodeText, ForeignKey('workflow_package_state.package_id', ondelete="CASCADE"),
               nullable=False),
        # Requester information
        Column('request_user_id', types.UnicodeText, ForeignKey('user.id', ondelete="CASCADE"), nullable=False),
        Column('request_state', types.UnicodeText, nullable=False),
        # Additional request information
        Column('request_message', types.UnicodeText, default=None, nullable=True),
        Column('request_timestamp', types.DateTime, default=datetime.datetime.now(), nullable=False),
        # Approver information
        Column('process_user_id', types.UnicodeText, ForeignKey('user.id', ondelete="CASCADE"), default=None,
               nullable=True),
        Column('process_message', types.UnicodeText, default=None, nullable=True),
        Column('process_timestamp', types.DateTime, default=None, nullable=True),
        Column('process_state', types.UnicodeText, default=REQUEST_STATE_PENDING, nullable=True),
    )
    Index(
        'workflow_package_request_only_one_active_request',
        workflow_package_request_table.c.package_id,
        workflow_package_request_table.c.request_state,
        workflow_package_request_table.c.process_state,
        unique=True,
        postgresql_where=workflow_package_request_table.c.process_state == REQUEST_STATE_PENDING
    )
    mapper(
        WorkflowPackageRequest,
        workflow_package_request_table,
        properties={
            '_state': orm.relationship(
                WorkflowPackageState, uselist=False,
                backref=orm.backref(
                    '_requests',
                    cascade='all, delete, delete-orphan'
                )
            ),
            '_requester': orm.relationship(
                User,
                primaryjoin=workflow_package_request_table.c.request_user_id == User.id,
                uselist=False
            ),
        },
    )
    return workflow_package_request_table
