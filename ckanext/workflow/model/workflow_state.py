# encoding: utf-8

'''Model.'''

from __future__ import print_function
import sqlalchemy.orm as orm
import sqlalchemy.types as types
from ckan.model import meta, Package, DomainObject
import ckan.model.types as _types
from sqlalchemy import Table, Column, ForeignKey, Index, CheckConstraint, ForeignKeyConstraint, UniqueConstraint
# logging
import logging
log = logging.getLogger(__name__)

mapper = orm.mapper


class WorkflowState(DomainObject):
    """

    """
    package_id = None
    state_id = None

    package = None
    requests = None

    @property
    def has_requests(self):
        """
        Returns if there are any requests associated with it
        :return: boolean if this state has any requests associated with it
        """
        return len(self.requests) > 0

    def __init__(self, package_id, state_id):
        super(WorkflowState, self).__init__(**{})
        self.package_id = package_id
        self.state_id = state_id

    @classmethod
    def all(cls):
        return meta.Session.query(cls).all()

    @classmethod
    def get(cls, package_id):
        """

        :param package_id:
        :return:
        """
        return meta.Session.query(cls).filter(cls.package_id == package_id).one_or_none()

    @classmethod
    def get_for_organization(cls, organization_id):
        query = meta.Session.query(cls)
        query = query.filter(cls.package.has(owner_org=organization_id))
        return query.all()


def define_workflow_state_table():
    workflow_state_table = Table(
        'workflow_state', meta.metadata,
        Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
        Column('package_id', types.UnicodeText, ForeignKey('package.id', ondelete="CASCADE"), unique=True),
        Column('state_id', types.UnicodeText, nullable=False),
    )
    mapper(WorkflowState, workflow_state_table,
           properties={
               'package': orm.relationship(Package, uselist=False)
           }, )
    return workflow_state_table
