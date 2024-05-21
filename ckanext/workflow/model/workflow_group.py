# encoding: utf-8

'''Model.'''

from __future__ import print_function
import sqlalchemy.orm as orm
import sqlalchemy.types as types
from ckan.model import meta, Group, DomainObject
import ckan.model.types as _types
from sqlalchemy import Table, Column, ForeignKey, Index, CheckConstraint, ForeignKeyConstraint, UniqueConstraint
# logging
import logging
log = logging.getLogger(__name__)

mapper = orm.mapper


class WorkflowGroup(DomainObject):
    """

    """
    group_id = None
    enabled = None

    group = None

    def __init__(self, group_id, enabled):
        self.group_id = group_id
        self.enabled = enabled

    @classmethod
    def all(cls):
        return meta.Session.query(cls).all()

    @classmethod
    def get(cls, group_id):
        """

        :param package_id:
        :return:
        """
        return meta.Session.query(cls).filter(cls.group_id == group_id).one_or_none()


def define_workflow_group_table():
    workflow_group_table = Table(
        'workflow_group', meta.metadata,
        Column('group_id', types.UnicodeText, ForeignKey('group.id', ondelete="CASCADE"), primary_key=True),
        Column('enabled', types.Boolean, nullable=False),
    )
    mapper(WorkflowGroup, workflow_group_table,
           properties={
               'group': orm.relationship(Group, uselist=False)
           }, )
    return workflow_group_table
