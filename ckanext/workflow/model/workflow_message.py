# encoding: utf-8

'''Model.'''

from sqlalchemy.orm import mapper, relationship, foreign, remote, aliased
from sqlalchemy.types import UnicodeText
from sqlalchemy import Table, Column, ForeignKey, and_, func, select
from sqlalchemy.ext.hybrid import hybrid_property
from ckan.model import User, Activity
from ckan.model.meta import metadata
from sqlalchemy import select, literal, cast, String, union_all, func, literal_column
from sqlalchemy import select, literal, cast, String, union_all, func, literal_column

from ckanext.workflow.model.workflow_object import WorkflowObject
from ckanext.workflow.common import getLogger


log = getLogger(__name__)


class WorkflowMessage(WorkflowObject):

    user_id = None
    content = None
    reference_type = None
    reference_id = None

    @property
    def replies(self):
        return self._replies
    
    @hybrid_property
    def num_replies(self):
        return len(self._replies)
    
    @num_replies.expression
    def num_replies(cls):
        ReplyMessage = aliased(WorkflowMessage)
        return select([func.count(ReplyMessage.id)]).\
            where(and_(ReplyMessage.reference_id == literal_column('workflow_message.id'), ReplyMessage.reference_type == WorkflowMessage.get_object_type_name())).\
            as_scalar()

    @property
    def activities(self):
        return self._activities
    
    @hybrid_property
    def latest_activity(self):
        options = [max((r.timestamp for r in self._activities), default=None), self.modified, self.created]
        return next(o for o in options if o is not None)
    
    @latest_activity.expression
    def latest_activity(cls):
        modified = literal_column('workflow_message.modified')
        created = literal_column('workflow_message.created')
        id = literal_column('workflow_message.id')
        return select([func.coalesce(func.coalesce(func.max(Activity.timestamp), modified), created)]).where(id == Activity.object_id).as_scalar()
        # return select([func.coalesce(func.coalesce(func.max(Activity.timestamp), cls.modified), cls.created)]).where(cls.id == Activity.object_id).as_scalar()

    def as_dict(self, context):
        result = super(WorkflowMessage, self).as_dict(context)
        result['num_replies'] = self.num_replies
        result['latest_activity'] = self.latest_activity
        return result


def define_workflow_message_table() -> Table:
    """
    This will define the workflow_state Table and map it to both WorkflowState and Package
    :return: Table
    """
    workflow_message_table = Table(
        'workflow_message', metadata,
        *WorkflowMessage.get_default_columns(),
        Column('user_id', UnicodeText, ForeignKey('user.id', ondelete="CASCADE"), nullable=False),
        Column('content', UnicodeText, default=None, nullable=False),
        Column('reference_type', UnicodeText, default=None, nullable=False),
        Column('reference_id', UnicodeText, default=None, nullable=False)
    )

    mapper(WorkflowMessage, workflow_message_table,
           properties={
                '_user': relationship(
                    User,
                    primaryjoin=workflow_message_table.c.user_id == User.id,
                    uselist=False
                ),
                '_replies': relationship(
                    WorkflowMessage,
                    primaryjoin=and_(foreign(workflow_message_table.c.id) == remote(workflow_message_table.c.reference_id), remote(workflow_message_table.c.reference_type) == WorkflowMessage.get_object_type_name()),
                    uselist=True
                ),
                '_activities': relationship(
                    Activity,
                    primaryjoin=foreign(workflow_message_table.c.id) == remote(Activity.object_id),
                    uselist=True
                ),
           }, )
    return workflow_message_table
