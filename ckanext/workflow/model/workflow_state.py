# encoding: utf-8

'''Model.'''

from sqlalchemy.orm import mapper, relationship, foreign, remote
from sqlalchemy.types import UnicodeText, DateTime, Boolean
from sqlalchemy import Table, Column, ForeignKey, Enum, or_, literal_column, select
from typing import List, Optional
from typing_extensions import Self
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from ckanext.workflow.model.workflow_object import WorkflowObject

import logging
from ckan.model import DomainObject, Package, Session, Activity
from ckan.model.meta import metadata
from ckan.model.core import State

log = logging.getLogger(__name__)


class WorkflowState(WorkflowObject):
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

    @hybrid_property
    def owner_org(self):
        return self._package.owner_org
    
    @owner_org.expression
    def owner_org(cls):
        return select([Package.owner_org]).\
            where(Package.id == literal_column('workflow_state.package_id')).\
            as_scalar()
    
    @hybrid_property
    def package_state(self):
        return self._package.state
    
    @package_state.expression
    def package_state(cls):
        return select([Package.state]).\
            where(Package.id == literal_column('workflow_state.package_id')).\
            as_scalar()

    # @classmethod
    # def fields_filter(cls):
    #     return {
    #         'owner_org': lambda v : or_(*[cls._package.has(owner_org=e) for e in v]),
    #         'package_state': lambda v : or_(*[cls._package.has(state=e) for e in v]),
    #     }

    @classmethod
    def get(cls, package_id: str) -> Optional[Self]:
        """

        :param package_id:
        :type: str
        :return:
        :rtype: WorkflowState
        """
        return Session.query(cls).filter(cls.package_id == package_id).one_or_none()


def define_workflow_state_table() -> Table:
    """
    This will define the workflow_state Table and map it to both WorkflowState and Package
    :return: Table
    """
    workflow_state_table = Table(
        'workflow_state', metadata,
        *WorkflowState.get_default_columns(),
        Column('package_id', UnicodeText, ForeignKey('package.id'), nullable=False),
        Column('state_id', UnicodeText, nullable=False),
        Column('is_default', Boolean, default=True, nullable=False)
    )
    mapper(WorkflowState, workflow_state_table,
           properties={
               '_package': relationship(Package, uselist=False),
                '_activities': relationship(
                    Activity,
                    primaryjoin=foreign(workflow_state_table.c.id) == remote(Activity.object_id),
                    uselist=True
                ),
           }
    )
    return workflow_state_table
