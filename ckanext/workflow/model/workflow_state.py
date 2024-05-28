# encoding: utf-8

'''Model.'''

import sqlalchemy.orm as orm
import sqlalchemy.types as types
import ckan.model.types as _types
from sqlalchemy import Table, Column, ForeignKey, Index, CheckConstraint, ForeignKeyConstraint, UniqueConstraint

import logging
import ckan.model as model

log = logging.getLogger(__name__)

mapper = orm.mapper


class WorkflowPackageState(model.DomainObject):
    """

    """
    package_id = None
    state_id = None

    _package = None
    _requests = None

    @property
    def package(self):
        """

        :return: Package object related to this WorkflowPackageState
        :rtype: model.Package
        """
        return self._package

    @property
    def requests(self):
        """

        :return:
        :rtype: list of WorkflowPackageRequest
        """
        return self._requests

    @property
    def has_requests(self):
        """
        Returns if there are any requests associated with it
        :return: boolean if this state has any requests associated with it
        """
        return len(self.requests) > 0

    def __init__(self, package_id, state_id):
        super(WorkflowPackageState, self).__init__(**{})
        self.package_id = package_id
        self.state_id = state_id

    @classmethod
    def all(cls):
        return model.Session.query(cls).all()

    @classmethod
    def get(cls, package_id):
        """

        :param package_id:
        :return:
        :rtype: WorkflowPackageState
        """
        return model.Session.query(cls).filter(cls.package_id == package_id).one_or_none()

    @classmethod
    def get_for_organization(cls, organization_id):
        query = model.Session.query(cls)
        query = query.filter(cls.package.has(owner_org=organization_id))
        return query.all()


def define_workflow_package_state_table():
    workflow_package_state_table = Table(
        'workflow_package_state', model.meta.metadata,
        Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
        Column('package_id', types.UnicodeText, ForeignKey('package.id', ondelete="CASCADE"), unique=True),
        Column('state_id', types.UnicodeText, nullable=False),
    )
    mapper(WorkflowPackageState, workflow_package_state_table,
           properties={
               '_package': orm.relationship(model.Package, uselist=False)
           }, )
    return workflow_package_state_table
