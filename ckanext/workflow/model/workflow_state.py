# encoding: utf-8

'''Model.'''

from sqlalchemy.orm import mapper, relationship
from sqlalchemy.types import UnicodeText, DateTime, Boolean
from sqlalchemy import Table, Column, ForeignKey
from typing import List, Optional
from typing_extensions import Self
from datetime import datetime

import logging
from ckan.model import DomainObject, Package, Session
from ckan.model.meta import metadata

log = logging.getLogger(__name__)


class WorkflowState(DomainObject):
    package_id: str = None
    state_id: str = None
    _package = None

    @property
    def package(self) -> Package:
        """

        :return: Package object related to this WorkflowState
        :rtype: model.Package
        """
        return self._package

    def __init__(self, package_id: str, state_id: str, is_default : bool = False):
        super(WorkflowState, self).__init__(**{})
        self.package_id = package_id
        self.state_id = state_id
        self.is_default = is_default

    @classmethod
    def all(cls) -> List[Self]:
        """

        :return:
        """
        return Session.query(cls).all()

    @classmethod
    def get(cls, package_id: str) -> Optional[Self]:
        """

        :param package_id:
        :type: str
        :return:
        :rtype: WorkflowState
        """
        return Session.query(cls).filter(cls.package_id == package_id).one_or_none()

    @classmethod
    def get_for_organization(cls, organization_id: str) -> List[Self]:
        """

        :param organization_id: owner_org id
        :type: str

        :return: List of WorkflowState for all matching packages
        :rtype: list of WorkflowState
        """
        query = Session.query(cls)
        query = query.filter(cls.package.has(owner_org=organization_id))
        return query.all()


def define_workflow_state_table() -> Table:
    """
    This will define the workflow_state Table and map it to both WorkflowState and Package
    :return: Table
    """
    workflow_state_table = Table(
        'workflow_state', metadata,
        Column('package_id', UnicodeText, ForeignKey('package.id', ondelete="CASCADE"), primary_key=True),
        Column('state_id', UnicodeText, nullable=False),
        Column('created', DateTime, default=datetime.now(), nullable=False),
        Column('modified', DateTime, default=None, nullable=True),
        Column('is_default', Boolean, default=False, nullable=False)
    )
    mapper(WorkflowState, workflow_state_table,
           properties={
               '_package': relationship(Package, uselist=False)
           }, )
    return workflow_state_table
