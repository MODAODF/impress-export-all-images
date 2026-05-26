#!/usr/bin/env python3

import datetime
from com.sun.star.util import Time, Date, DateTime
from easymacro import create_instance, Paths
from peewee import Database, DateTimeField, DateField, TimeField, \
    __exception_wrapper__


def _date_to_struct(value):
    if isinstance(value, datetime.datetime):
        d = DateTime()
        d.Year = value.year
        d.Month = value.month
        d.Day = value.day
        d.Hours = value.hour
        d.Minutes = value.minute
        d.Seconds = value.second
    elif isinstance(value, datetime.date):
        d = Date()
        d.Day = value.day
        d.Month = value.month
        d.Year = value.year
    elif isinstance(value, datetime.time):
        d = Time()
        d.Hours = value.hour
        d.Minutes = value.minute
        d.Seconds = value.second
    return d


def _struct_to_date(value):
    d = None
    if isinstance(value, Time):
        d = datetime.time(value.Hours, value.Minutes, value.Seconds)
    elif isinstance(value, Date):
        if value != Date():
            d = datetime.date(value.Year, value.Month, value.Day)
    elif isinstance(value, DateTime):
        if value.Year > 0:
            d = datetime.datetime(
                value.Year, value.Month, value.Day,
                value.Hours, value.Minutes, value.Seconds)
    return d


class BaseDateField(DateField):

    def db_value(self, value):
        return _date_to_struct(value)

    def python_value(self, value):
        return _struct_to_date(value)


class BaseTimeField(TimeField):

    def db_value(self, value):
        return _date_to_struct(value)

    def python_value(self, value):
        return _struct_to_date(value)


class BaseDateTimeField(DateTimeField):

    def db_value(self, value):
        return _date_to_struct(value)

    def python_value(self, value):
        return _struct_to_date(value)


class FirebirdDatabase(Database):
    field_types = {'BOOL': 'BOOLEAN', 'DATETIME': 'TIMESTAMP'}

    def __init__(self, database, **kwargs):
        super().__init__(database, **kwargs)
        self._db = database

    def _connect(self):
        return self._db

    def create_tables(self, models, **options):
        options['safe'] = False
        tables = self._db.tables
        models = [m for m in models if not m.__name__.lower() in tables]
        super().create_tables(models, **options)

    def execute_sql(self, sql, params=None, commit=True):
        with __exception_wrapper__:
            cursor = self._db.execute(sql, params)
        return cursor

    def last_insert_id(self, cursor, query_type=None):
        # ~ debug('LAST_ID', cursor)
        return 0

    def rows_affected(self, cursor):
        return self._db.rows_affected

    @property
    def path(self):
        return self._db.path


class LODocBase(object):
    _type = 'base'
    DB_TYPES = {
        str: 'setString',
        int: 'setInt',
        float: 'setFloat',
        bool: 'setBoolean',
        Date: 'setDate',
        Time: 'setTime',
        DateTime: 'setTimestamp',
    }
    # ~ setArray
    # ~ setBinaryStream
    # ~ setBlob
    # ~ setByte
    # ~ setBytes
    # ~ setCharacterStream
    # ~ setClob
    # ~ setNull
    # ~ setObject
    # ~ setObjectNull
    # ~ setObjectWithInfo
    # ~ setPropertyValue
    # ~ setRef

    def __init__(self, obj, args={}):
        self._obj = obj
        self._dbc = create_instance('com.sun.star.sdb.DatabaseContext')
        self._rows_affected = 0
        path = args.get('path', '')
        self._path = Paths(path)
        self._name = self._path.name
        if Paths.exists(path):
            if not self.is_registered:
                self.register()
            db = self._dbc.getByName(self.name)
        else:
            db = self._dbc.createInstance()
            db.URL = 'sdbc:embedded:firebird'
            db.DatabaseDocument.storeAsURL(self._path.url, ())
            self.register()
        self._obj = db
        self._con = db.getConnection('', '')

    def __contains__(self, item):
        return item in self.tables

    @property
    def obj(self):
        return self._obj

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return str(self._path)

    @property
    def is_registered(self):
        return self._dbc.hasRegisteredDatabase(self.name)

    @property
    def tables(self):
        tables = [t.Name.lower() for t in self._con.getTables()]
        return tables

    @property
    def rows_affected(self):
        return self._rows_affected

    def register(self):
        if not self.is_registered:
            self._dbc.registerDatabaseLocation(self.name, self._path.url)
        return

    def revoke(self, name):
        self._dbc.revokeDatabaseLocation(name)
        return True

    def save(self):
        self.obj.DatabaseDocument.store()
        self.refresh()
        return

    def close(self):
        self._con.close()
        return

    def refresh(self):
        self._con.getTables().refresh()
        return

    def initialize(self, database_proxy, tables=[]):
        db = FirebirdDatabase(self)
        database_proxy.initialize(db)
        if tables:
            db.create_tables(tables)
        return

    def _validate_sql(self, sql, params):
        limit = ' LIMIT '
        for p in params:
            sql = sql.replace('?', f"'{p}'", 1)
        if limit in sql:
            sql = sql.split(limit)[0]
            sql = sql.replace('SELECT', f'SELECT FIRST {params[-1]}')
        return sql

    def cursor(self, sql, params):
        if sql.startswith('SELECT'):
            sql = self._validate_sql(sql, params)
            cursor = self._con.prepareStatement(sql)
            return cursor

        if not params:
            cursor = self._con.createStatement()
            return cursor

        cursor = self._con.prepareStatement(sql)
        for i, v in enumerate(params, 1):
            t = type(v)
            if not t in self.DB_TYPES:
                error('Type not support')
                debug((i, t, v, self.DB_TYPES[t]))
            getattr(cursor, self.DB_TYPES[t])(i, v)
        return cursor

    def execute(self, sql, params):
        debug(sql, params)
        cursor = self.cursor(sql, params)

        if sql.startswith('SELECT'):
            result = cursor.executeQuery()
        elif params:
            result = cursor.executeUpdate()
            self._rows_affected = result
            self.save()
        else:
            result = cursor.execute(sql)
            self.save()

        return result

    def select(self, sql):
        debug('SELECT', sql)
        if not sql.startswith('SELECT'):
            return ()

        cursor = self._con.prepareStatement(sql)
        query = cursor.executeQuery()
        return BaseQuery(query)

    def get_query(self, query):
        sql, args = query.sql()
        sql = self._validate_sql(sql, args)
        return self.select(sql)
