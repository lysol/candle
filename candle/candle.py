from functools import wraps
import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.extensions import adapt, register_adapter, AsIs


def defaultcommit(f):
    """Decorator function to provide behavior of committing after
    a DML operation"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        commit = True 
        if 'commit' in kwargs:
            if kwargs['commit']:
                commit = kwargs['commit']
                del kwargs['commit']
        result = f(*args, **kwargs)
        if commit: 
            args[0].commit()
        return result
    return wrapper


def enablecache(f):
    """Decorator to cache the results of the method on first
    execution."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not hasattr(args[0], '_cache'):
            setattr(args[0], '_cache', {})
        elif f.__name__ in args[0]._cache:
            return args[0]._cache[f.__name__]
        result = f(*args, **kwargs)
        args[0]._cache[f.__name__] = result
        return result
    return wrapper


class RawValue(str):
    pass

def adapt_raw(raw):
    return AsIs("%s" % raw)

register_adapter(RawValue, adapt_raw)

class Candle(dict):

    _id_column = 'id'
    table_name = None
    conn = None
    connstring = None
    
    @property
    def id(self):
        return self[self._id_column]

    @classmethod
    def set_conn(cls, connstring=None):
        if connstring is None:
            connstring = cls.connstring
        if type(connstring) == str:
            cls.conn = psycopg2.connect(connstring)
        else:
            cls.conn = connstring

    @classmethod
    def set_connstring(cls, connstring):
        cls.connstring = connstring

    def __init__(self, *args, **kwargs):
        if type(self.table_name) != str:
            raise Exception("Table name is not a string: %s" % table_name)
        super(Candle, self).__init__(*args, **kwargs)

    @classmethod
    def commit(cls):
        cls.conn.commit()

    @classmethod
    def cursor(cls):
        return cls.conn.cursor(cursor_factory=DictCursor)

    def __getstate__(self):
        return {
                'table_name': self.table_name,
                'data': dict(self.items()),
                'connstring': self.connstring
        }

    def __setstate__(self, state):
        self.table_name = state['table_name']
        self.update(state['data'])
        self.connstring = state['connstring']

    def __setattr__(self, key, val):
        if key in self:
            self[key] = val
        elif hasattr(self, key) or key in \
            ['table_name', 'conn', 'connstring', '_cache']:
            super(Candle, self).__setattr__(key, val)

    def __getattr__(self, key):
        if key in self:
            return self[key]
        else:
            return object.__getattribute__(self, key)

    def update(self, indict):
        for key in indict:
            setattr(self, key, indict[key])
    
    @classmethod
    def _fields(cls):
        query = """
            SELECT column_name
            FROM information_schema 
            WHERE table_catalog = current_database()
            AND table_name = %s
            """
        cursor = cls.cursor()
        cursor.execute(query, [cls.table_name])
        return [r['column_name'] for r in cursor.fetchall()]

    @classmethod
    @defaultcommit
    def new(cls, data={}):
        cursor = cls.cursor()
        fieldlist = ', '.join(['"%s"' % k for k in data.keys()])
        insertclause = ', '.join([str(adapt(data[k])) for k in data.keys()])
        cursor.execute("""
            INSERT INTO %s (%s) VALUES (%s) RETURNING *
            """ % (cls.table_name, fieldlist, insertclause))
        result = cursor.fetchone()
        return cls(result)

    @defaultcommit
    def save(self):
        cursor = self.cursor()
        updateclause = ", ".join(
                ['"%s" = %s' % (k, adapt(self[k])) for k \
                        in self]
                )
        cursor.execute("""
            UPDATE %s SET %s
            WHERE "%s" = %s
            RETURNING *
            """ % (self.table_name, updateclause,
                self._id_column, adapt(self[self._id_column])))
        result = cursor.fetchone()
        for key in result.keys():
            self[key] = result[key]

    @defaultcommit
    def delete(self):
        cursor = self.cursor()
        cursor.execute("""
            DELETE FROM %s
            WHERE "%s" = %s
            """ % (self.table_name, self._id_column,
                adapt(self[self._id_column])))

    @classmethod
    def get(cls, id):
        cursor = cls.cursor()
        cursor.execute("""
            SELECT * FROM "%s"
            WHERE "%s" = %%s
            """ % (cls.table_name, cls._id_column),
            [id]
            )
        result = cursor.fetchone()
        return cls(result)

    @classmethod
    def get_many(cls, ids):
        cursor = cls.cursor()
        orclause = " OR ".join(
            ['"%s" = %s' % (cls._id_column, adapt(id)) for id in ids])
        cursor.execute("""
            SELECT * FROM "%s"
            WHERE %s
            """ % (cls.table_name, orclause)
            )
        return [cls(x) for x in cursor.fetchall()]

    @classmethod
    def where(cls, conditions, joiner='AND'):
        conditionclause = (" %s " % joiner).join(
                ['"%s" = %s' % (k, adapt(conditions[k])) for \
                k in conditions])
        cursor = cls.cursor()
        cursor.execute("""
            SELECT * FROM "%s"
            WHERE %s
            """ % (cls.table_name, conditionclause))
        return [cls(x) for x in cursor.fetchall()]

    @classmethod
    def exists(cls, conditions, joiner='AND'):
        conditionclause = (" %s " % joiner).join(
                ['"%s" = %s' % (k, adapt(conditions[k])) for \
                k in conditions])
        cursor = cls.cursor()
        cursor.execute("""
            SELECT EXISTS(SELECT TRUE FROM "%s"
            WHERE %s) AS "exists" LIMIT 1
            """ % (cls.table_name, conditionclause))
        return cursor.fetchone()['exists']
