# encoding: utf-8

'''Model.'''

from sqlalchemy.orm import mapper, relationship
from sqlalchemy.types import UnicodeText, DateTime
from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from ckan.model import User, DomainObject
from ckan.model.types import make_uuid
from ckan.model.meta import metadata

import logging
import datetime



log = logging.getLogger(__name__)


class WorkflowRequestMessage(DomainObject):
    id = None
    request_id = None
    user_id = None
    created = None
    modified = None
    content = None
    suggestion = None

    def __init__(self, request_id, user_id, **kwargs):
        super(WorkflowRequestMessage, self).__init__(**kwargs)
        self.id = make_uuid()
        self.request_id = request_id
        self.user_id = user_id

    def save_activity(self, context, activity_type='updated'):
        model = context["model"]
        session = context["session"]
        actor = model.User.by_name(context["user"])
        activity = model.Activity(
            actor.id, self.id, "{} request".format(activity_type),
            {'request_message': self.as_dict(), 'actor': actor.name}
        )
        print("adding new Activity to session")
        session.add(activity)

    def save_context(self, context, add_activity=True, activity_type='updated'):
        session = context["session"]
        print("adding new WorkflowRequestMessage to session")
        session.add(self)
        if add_activity:
            self.save_activity(context, activity_type)
        if not context.get('defer_commit'):
            session.commit()
        return self

    @classmethod
    def create(cls, context, data_dict, add_activity=True):
        return cls(**data_dict).save_context(context, add_activity, 'new')

    def changes(self, data_dict):
        return [key for key in data_dict if getattr(self, key) != data_dict[key]]

    @classmethod
    def update(cls, context, data_dict, add_activity=True, activity_type='updated'):
        workflow_request_message = cls.get(data_dict["id"])
        changes = workflow_request_message.changes(data_dict)
        print(f"update {workflow_request_message} {changes}")
        if changes:
            for key in data_dict:
                setattr(workflow_request_message, key, data_dict[key])
            workflow_request_message.modified = datetime.datetime.now(datetime.timezone.utc)
            workflow_request_message.save_context(context, add_activity, activity_type)
        return workflow_request_message


def define_workflow_request_message_table() -> Table:
    """
    This will define the workflow_state Table and map it to both WorkflowState and Package
    :return: Table
    """
    workflow_request_message_table = Table(
        'workflow_request_message', metadata,
        Column('id', UnicodeText, primary_key=True, default=make_uuid()),
        Column('request_id', UnicodeText, ForeignKey('workflow_request.id', ondelete="CASCADE"), primary_key=True),
        Column('user_id', UnicodeText, ForeignKey('user.id'), nullable=True),
        Column('created', DateTime, default=datetime.datetime.now(), nullable=False),
        Column('modified', DateTime, default=None, nullable=True),
        Column('content', UnicodeText, default=None, nullable=False),
        Column('suggestion', JSONB, default=None, nullable=True)
    )
    mapper(WorkflowRequestMessage, workflow_request_message_table,
           properties={
                '_user': relationship(
                    User,
                    primaryjoin=workflow_request_message_table.c.user_id == User.id,
                    uselist=False
                )
           }, )
    return workflow_request_message_table
