# encoding: utf-8

'''Model.'''

from sqlalchemy.orm import mapper, relationship, backref, foreign, remote, aliased
from sqlalchemy.types import UnicodeText, DateTime
from ckan.model import User, Package, DomainObject, Session, Activity
from ckan.model.meta import metadata
from ckanext.workflow.model.workflow_state import WorkflowState
from ckanext.workflow.model.workflow_message import WorkflowMessage
from ckanext.workflow.model.workflow_object import WorkflowObject
from ckan.model.types import make_uuid, JsonDictType
import ckan.model as model
import datetime
from sqlalchemy import Table, Column, ForeignKey, Index, desc, asc, or_, and_, cast, Enum, select
# logging
import logging

log = logging.getLogger(__name__)

# list of states
REQUEST_STATE_PENDING = 'pending'
REQUEST_STATE_APPROVED = 'approved'
REQUEST_STATE_REJECTED = 'rejected'
REQUEST_STATE_CLOSED = 'closed'
REQUEST_STATE_RESOLVED = 'resolved'

# list of states meaning a request is still waiting for a reaction)
REQUEST_OPEN_STATES = [REQUEST_STATE_PENDING]
# list of states meaning a request is closed due to a reaction
REQUEST_HANDLED_STATES = [REQUEST_STATE_APPROVED, REQUEST_STATE_REJECTED]
# list of states meaning a request is closed because something which made the request invalid
REQUEST_IGNORED_STATES = [REQUEST_STATE_CLOSED, REQUEST_STATE_RESOLVED]
REQUEST_STATES = REQUEST_OPEN_STATES + REQUEST_HANDLED_STATES + REQUEST_IGNORED_STATES


class WorkflowRequest(WorkflowObject):
    # list of all the columns to make them recognized by the IDE
    id = None
    package_id = None
    request_user_id = None
    request_state = None
    request_timestamp = None
    process_user_id = None
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
    def processer(self):
        return self._processer

    @property
    def package(self):
        return self.state.package

    @property
    def messages(self):
        return self._messages

    @property
    def is_open(self):
        return self.process_state in REQUEST_OPEN_STATES

    @property
    def is_handled(self):
        return self.process_state in REQUEST_HANDLED_STATES

    @property
    def is_ignored(self):
        return self.process_state in REQUEST_IGNORED_STATES

    @property
    def is_approved(self):
        return self.process_state == REQUEST_STATE_APPROVED

    @property
    def is_rejected(self):
        return self.process_state == REQUEST_STATE_REJECTED


    @classmethod
    def states(cls, open=None, handled=None, ignored=None):

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

    def __init__(self, package_id, current_state, request_user_id, request_state, **kwargs):
        super(WorkflowRequest, self).__init__(**kwargs)
        self.id = make_uuid()
        self.package_id = package_id
        self.current_state = current_state
        self.request_user_id = request_user_id
        self.request_state = request_state

    @classmethod
    def all(cls):
        return Session.query(cls).all()

    @classmethod
    def get(cls, id):
        return Session.query(cls).filter(cls.id == id).one_or_none()

    @classmethod
    def query_for_package(cls, package_id):
        query = Session.query(cls)
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
        query = Session.query(cls)
        query = query.filter(cls.state.package.has(owner_org=owner_org))
        return query.all()

    def set_process(self, process_state, process_user_id, process_timestamp=None):
        self.process_state = process_state
        self.process_user_id = process_user_id
        self.process_timestamp = datetime.datetime.utcnow() if process_timestamp is None else process_timestamp

    def set_resolved(self, user_id):
        self.set_process(REQUEST_STATE_RESOLVED, user_id)

    def set_closed(self, user_id):
        self.set_process(REQUEST_STATE_CLOSED, user_id)

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
        session = context["session"]
        print("adding new WorkflowRequest to session")
        session.add(self)
        if add_activity:
            self.save_activity(context, activity_type)
        if not context.get('defer_commit'):
            session.commit()
        return self

    @classmethod
    def create(cls, context, data_dict, add_activity=True):
        workflow_request = cls(**data_dict)
        return workflow_request.save_context(context, add_activity, 'new')

    def changes(self, data_dict):
        return [key for key in data_dict if getattr(self, key) != data_dict[key]]

    @classmethod
    def update(cls, context, data_dict, add_activity=True, activity_type='updated'):
        workflow_request = cls.get(data_dict["id"])
        changes = workflow_request.changes(data_dict)
        print(f"update {workflow_request} {changes}")
        if changes:
            for key in data_dict:
                setattr(workflow_request, key, data_dict[key])
            workflow_request.modified_timestamp = datetime.datetime.utcnow()
            if ("process_state" in changes and workflow_request.process_state not in REQUEST_OPEN_STATES and
                    not workflow_request.process_timestamp):
                workflow_request.process_timestamp = datetime.datetime.utcnow()
            workflow_request.save_context(context, add_activity, activity_type)
        return workflow_request

    @classmethod
    def get_for_user(cls, user_id, open, closed, approved, as_requester, as_approver):
        query = Session.query(cls)
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

    def get_activities(self, limit, offset, include_package_activities=True):
        filter = [model.Activity.object_id == self.id]
        if include_package_activities:
            package_activity = [model.Activity.object_id == self.package_id, model.Activity.timestamp > self.request_timestamp]
            if not self.is_open:
                package_activity.append(model.Activity.timestamp <= self.process_timestamp)
            filter.append(and_(*package_activity))
        query = model.Session.query(model.Activity).filter(
            or_(*filter)
        ).order_by(asc(model.Activity.timestamp))
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()

    def as_dict(self, include_messages=True, include_users=True):
        result = super(WorkflowRequest, self).as_dict()
        if include_messages:
            result['messages'] = [m.as_dict() for m in self.messages]
        if include_users:
            result['requester'] = self.requester.as_dict() if self.requester else None
            result['processor'] = self.processor.as_dict() if self.processor else None
        return result


def define_workflow_request_table():
    workflow_request_table = Table(
        'workflow_request',
        metadata,
        # generic identifier
        *WorkflowRequest.get_default_columns(),
        Column('package_id', UnicodeText, ForeignKey('package.id', ondelete="CASCADE"), nullable=False),
        Column('from_state_id', UnicodeText, nullable=False),
        # Requester information
        Column('user_id', UnicodeText, ForeignKey('user.id', ondelete="CASCADE"), nullable=False),
        Column('to_state_id', UnicodeText, nullable=False),
        # Additional request information
        Column('processed_user_id', UnicodeText, ForeignKey('user.id', ondelete="CASCADE"), default=None, nullable=True),
        Column('processed_timestamp', DateTime, default=None, nullable=True),
        Column('processed_state', UnicodeText, default=REQUEST_STATE_PENDING, nullable=True),
    )
    Index(
        'workflow_request_index_2',
        workflow_request_table.c.package_id,
        workflow_request_table.c.from_state_id,
        workflow_request_table.c.to_state_id
    )
    Index(
        'workflow_request_only_one_active_request',
        workflow_request_table.c.package_id,
        workflow_request_table.c.from_state_id,
        workflow_request_table.c.to_state_id,
        workflow_request_table.c.processed_state,
        unique=True,
        postgresql_where=workflow_request_table.c.processed_state == REQUEST_STATE_PENDING
    )
    mapper(
        WorkflowRequest,
        workflow_request_table,
        properties={
            '_state': relationship(
                WorkflowState,
                uselist=False,
                primaryjoin=foreign(workflow_request_table.c.package_id) == remote(WorkflowState.package_id)
            ),
            '_package': relationship(Package, uselist=False),
            '_requester': relationship(
                User,
                primaryjoin=workflow_request_table.c.user_id == User.id,
                uselist=False
            ),
            '_processor': relationship(
                User,
                primaryjoin=workflow_request_table.c.processed_user_id == User.id,
                uselist=False
            ),
            '_messages': relationship(
                WorkflowMessage, 
                primaryjoin=and_(foreign(workflow_request_table.c.id) == remote(WorkflowMessage.reference_id), WorkflowMessage.reference_type == WorkflowRequest.get_object_type_name()),
                uselist=True
            ),
            '_activities': relationship(
                Activity,
                primaryjoin=foreign(workflow_request_table.c.id) == remote(Activity.object_id),
                uselist=True
            ),
        },
    )
    return workflow_request_table
