# encoding: utf-8

'''Model.'''

from sqlalchemy import text, Enum
import logging
from ckan.model import DomainObject, meta, Activity
from sqlalchemy.orm import mapper, relationship, class_mapper
from sqlalchemy.types import UnicodeText, DateTime, Boolean
from sqlalchemy import Table, Column, ForeignKey, Enum, or_, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import literal
from sqlalchemy.sql import func, expression
from typing import List, Optional
from typing_extensions import Self
import datetime
from ckan.model.types import make_uuid, JsonDictType
import ckanext.workflow.common as common

from sqlalchemy import create_engine, Table, Column, Integer, String, DateTime, MetaData, func, cast, literal_column, select, text
from sqlalchemy.sql.expression import literal, alias, lateral

from sqlalchemy import select, literal, cast, String, union_all, func, literal_column
from sqlalchemy.orm import aliased
from sqlalchemy.dialects import postgresql

log = logging.getLogger(__name__)


class WorkflowObject:

    created = None
    modified = None
    state = None

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    @hybrid_property
    def last_updated(self):
        return self.get_latest_activity_by_type('timestamp', 'updated')
    
    @last_updated.expression
    def last_updated(cls):
        return cls.get_latest_activity_by_type_expression('timestamp', 'updated')

    @hybrid_property
    def last_updated_by(self):
        return self.get_latest_activity_by_type('user_id', 'updated')
    
    @last_updated_by.expression
    def last_updated_by(cls):
        return cls.get_latest_activity_by_type_expression('user_id', 'updated')

    @classmethod
    def query(cls, limit=None, offset=None, order_by=None, **filter_args):
        session = meta.Session
        q = session.query(cls)
        q = cls.filter(q, session, **filter_args)
        q = cls.order(q, session, order_by)
        q = cls.paginate(q, session, limit, offset)
        return q

    @classmethod
    def facet(cls, fields=None, limit=None, mincount=None, **filter_args):

        if not fields:
            return []

        print(f"facet -> {fields} {limit} {mincount} {filter_args}")
        _fields = cls.facet_fields()

        facet_selects = []
        for field in fields:
            if field in _fields:
                if _fields[field]['attr_type'] == 'hybrid_property':
                    # attr = cls.__dict__.get(field)
                    # expr = attr.expr(cls)
                    compiled = _fields[field]['attr'].compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
                    facet_field = literal_column(str(compiled))
                else:
                    facet_field = literal_column(field)
                facet_selects.append(select([literal(field).label("facet_name"), cast(facet_field, String).label("facet_value")]))
            else:
                log.warning(f"facet field {field} not found")

        if not facet_selects:
            return []

        session = meta.Session

        facets_union = union_all(*facet_selects)
        facets_subq = facets_union.lateral('facets')

        facet_query = session.query(
                    facets_subq.c.facet_name.label('facet'),
                    facets_subq.c.facet_value.label('value'),
                    func.count().label('total')
                ).\
                select_from(cls).\
                join(facets_subq, literal(True)).\
                group_by(facets_subq.c.facet_name, facets_subq.c.facet_value)
        
        if filter_args:
            facet_query = cls.filter(facet_query, session, **filter_args)
        
        if mincount:
            facet_query = facet_query.having(func.count() > mincount)

        if limit:
            facet_query = facet_query.subquery()
            rank = session.query(facet_query, func.row_number().over(order_by=[facet_query.c.total.desc(),facet_query.c.value.asc()], partition_by=facet_query.c.facet).label('rnk')).subquery()
            query = session.query(rank.c.facet, rank.c.value, rank.c.total).filter(rank.c.rnk <= limit)

        else:
            query = facet_query

        return query

    @classmethod
    def get_table(cls):
        return class_mapper(cls).mapped_table

    @classmethod
    def get_columns(cls):
        return cls.get_table().c

    @classmethod
    def get_column_names(cls):
        return [column.name for column in cls.get_columns()]

    @classmethod
    def has_column(cls, name):
        return name in cls.get_column_names()

    @classmethod
    def filter(cls, query, session, **kwargs):
        _fields = cls.filter_fields()

        for key, value in kwargs.items():

            # field can be ..., ..., or ...
            set_filter = False
                        
            if key in _fields:
                set_filter = True
                query = query.filter(_fields[key]['attr'].in_([value] if not isinstance(value, list) else value))
                # query = query.filter(getattr(cls, key).in_([value] if not isinstance(value, list) else value))
            elif key.endswith(('_from', '_to')):
                *field, comparator = key.rsplit('_', 1)
                if field and field[0] in _fields:
                    field = _fields[field]['attr']
                    # field = getattr(cls, field[0])
                    if comparator == 'to':
                        set_filter = True
                        query = query.filter(field <= value)
                    elif comparator == 'from':
                        set_filter = True
                        query = query.filter(field >= value)

            if not set_filter:
                log.warning(f'Did no add filter based on {key} {value}')
        return query

    @classmethod
    def get(cls, reference, for_update=False):
        return meta.Session.query(cls).get(reference) if reference else None

    @classmethod
    def paginate(cls, query, session, limit=None, offset=None):
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query

    @classmethod
    def fields(cls):

        def default_field(attr, attr_type):
            return {
                'python_type': attr.type.python_type,
                'type': attr.type,
                'attr_type': attr_type,
                'attr': attr,
                'order': True,
                'filter': True,
                'facet': True
            }
        result = {
            c.name: default_field(c, 'column') for c in cls.get_columns()
        }
        for base in cls.__mro__:
            for name, attr in base.__dict__.items():
                if isinstance(attr, hybrid_property):
                    try:
                        # Call expr(cls) to bind to the current mapped class
                        expr = attr.expr(cls)
                        result[name] = default_field(expr, 'hybrid_property')
                    except AttributeError:
                        # If expr() not defined, skip
                        pass

        return result
    
    @classmethod
    def _fields_for(cls, t, default=False):
        return {k: v for k,v in cls.fields().items() if v.get(t, default)}
    
    @classmethod
    def order_fields(cls):
        return cls._fields_for('order')
    
    @classmethod
    def filter_fields(cls):
        return cls._fields_for('filter')
    
    @classmethod
    def facet_fields(cls):
        return cls._fields_for('facet')

    @classmethod
    def order(cls, query, session, order_by=None):
        if not order_by:
            return query
        _fields = cls.order_fields()
        sorts = []
        for sort in order_by:
            field, *direction = sort.split(' ', 1)
            direction = direction[0] if direction else 'asc'

            if field not in _fields:
                log.warning("gfsdgdsfg")
                continue
            else:
                order = _fields[field]['attr']
                # if _fields[field]['attr_type'] == 'hybrid_property':
                #     order = getattr(cls, field).expr(cls)
                # else:
                #     order = getattr(cls, field)

            if direction == 'desc':
                order = order.desc()
            else:
                order = order.asc()

            sorts.append(order)
        query = query.order_by(*sorts)
        return query

    @classmethod
    def get_default_columns(cls):
        return [
            Column('id', UnicodeText, primary_key=True, default=make_uuid),
            Column('created', DateTime, server_default=func.now(), nullable=False),
            Column('modified', DateTime, default=None, nullable=True, onupdate=func.now()),
            Column('state', Enum('active', 'deleted', name='state', native_enum=False), default='active', nullable=False),
        ]

    def save_activity(self, context, activity_type='updated'):
        model = context["model"]
        session = context["session"]
        actor = model.User.by_name(context["user"])
        object_type_name = self.__class__.get_object_type_name()
        activity = model.Activity(
            actor.id, self.id, "{} {}".format(activity_type, object_type_name),
            {object_type_name: self.as_dict(context), 'actor': actor.name}
        )
        print("adding new Activity to session")
        session.add(activity)

    def save_context(self, context, add_activity=True, activity_type='updated'):
        session = context["session"]
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
    def delete(cls, context, data_dict, add_activity=True):
        return cls.update(context, {'id': data_dict['id'], 'state': 'deleted'}, add_activity, 'deleted')

    @classmethod
    def purge(cls, context, data_dict):
        session = context["session"]
        obj = cls.get(data_dict["id"])
        session.delete(obj)
        if not context.get('defer_commit'):
            session.commit()
        return obj

    @classmethod
    def update(cls, context, data_dict, add_activity=True, activity_type='updated'):
        obj = cls.get(data_dict["id"])
        changes = obj.changes(data_dict)
        if changes:
            for key in data_dict:
                setattr(obj, key, data_dict[key])
            obj.save_context(context, add_activity, activity_type)
        return obj

    @classmethod
    def get_object_type_name(cls):
        return cls.__name__[0].lower() + ''.join(['_' + l.lower() if l.isupper() else l for l in cls.__name__[1:]])

    def as_dict(self, context):
        result = common.table_dictize(self, context)
        result['last_updated'] = self.last_updated
        result['last_updated_by'] = self.last_updated_by
        return result

    def get_latest_activity_by_type(self, attr=None, activity_type=None):
        if not self._activities:
            return None
        else:
            return next(
                ( 
                    getattr(a, attr) if attr else a for a in sorted(self._activities, key=lambda _a: _a.timestamp, reverse=True)
                    if activity_type is None or a.activity_type == f"{activity_type} {self.__class__.get_object_type_name()}"
                ),
                None
            )

    @classmethod
    def get_latest_activity_by_type_expression(cls, attr, activity_type=None):
        print(f'{cls.get_table().name}.id')
        object = getattr(Activity, attr) if attr else Activity
        expression = select([object]).where(literal_column(f'{cls.get_table().name}.id') == Activity.object_id)
        if activity_type is not None:
            expression = expression.where(Activity.activity_type == f"{activity_type} {cls.get_object_type_name()}")
        return expression.order_by(Activity.timestamp.desc()).limit(1).as_scalar()
