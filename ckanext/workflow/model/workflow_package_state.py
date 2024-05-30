# encoding: utf-8

'''Model.'''

from sqlalchemy.orm import mapper, relationship
from sqlalchemy.types import UnicodeText
from sqlalchemy import Table, Column, ForeignKey
from typing import List, Optional
from typing_extensions import Self

import logging
from ckan.model import DomainObject, Package, Session
from ckan.model.meta import metadata

log = logging.getLogger(__name__)



class WorkflowPackageState(DomainObject):
    package_id: str = None
    _package = None
    _requests = None

    @property
    def package(self) -> Package:
        """

        :return: Package object related to this WorkflowPackageState
        :rtype: model.Package
        """
        return self._package

    @property
    def requests(self) -> List['ckanext.workflow.model.workflow_package_request.WorkflowPackageRequest']:
        """

        :return:
        :rtype: list of workflow_request.WorkflowPackageRequest
        """
        return self._requests

    @property
    def has_requests(self) -> bool:
        """
        Returns if there are any requests associated with it
        :return: boolean if this state has any requests associated with it
        """
        return len(self.requests) > 0

    def __init__(self, package_id: str, state_id: str):
        super(WorkflowPackageState, self).__init__(**{})
        self.package_id = package_id
        self.state_id = state_id

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
        :rtype: WorkflowPackageState
        """
        return Session.query(cls).filter(cls.package_id == package_id).one_or_none()

    @classmethod
    def get_for_organization(cls, organization_id: str) -> List[Self]:
        """

        :param organization_id: owner_org id
        :type: str

        :return: List of WorkflowPackageState for all matching packages
        :rtype: list of WorkflowPackageState
        """
        query = Session.query(cls)
        query = query.filter(cls.package.has(owner_org=organization_id))
        return query.all()


def define_workflow_package_state_table() -> Table:
    """
    This will define the workflow_package_state Table and map it to both WorkflowPackageState and Package
    :return: Table
    """
    workflow_package_state_table = Table(
        'workflow_package_state', metadata,
        Column('package_id', UnicodeText, ForeignKey('package.id', ondelete="CASCADE"), primary_key=True),
        Column('state_id', UnicodeText, nullable=False)
    )
    mapper(WorkflowPackageState, workflow_package_state_table,
           properties={
               '_package': relationship(Package, uselist=False)
           }, )
    return workflow_package_state_table
