import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.extensions import adapt

class Candle(dict):

    _id_column = 'id'
    table_name = None
    conn = None
    connstring = None

    @classmethod
    def set_conn(cls, connstring=None):
        if connstring is None:
            connstring = cls.connstring
        cls.conn = psycopg2.connect(connstring)

    @classmethod
    def set_connstring(cls, connstring):
        cls.connstring = connstring

    def __init__(self, *args, **kwargs):
        if type(self.table_name) != str:
            raise Exception("Table name is not a string: %s" % table_name)
        self.data = {}
        super(Candle, self).__init__(*args, **kwargs)

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
        self.conn = state['conn']

    def __setattr__(self, key, val):
        if key in self:
            self[key] = val
        elif hasattr(self, key) or key in ['table_name', 'conn', 'connstring']:
            super(Candle, self).__setattr__(key, val)

    def __getattr__(self, key):
        if key in self:
            return self[key]
        else:
            return object.__getattribute__(self, key)

    def save(self):
        cursor = self.cursor()
        updateclause = ", ".join(
                ['"%s" = %s' % (k, adapt(self.data[k]))]
                )
        cursor.execute("""
            UPDATE %s SET %s
            WHERE "%s" = %s
            """ % (self.table_name, updateclause,
                self._id_name, adapt(self.data[self._id_name])))

    def delete(self):
        cursor = self.cursor()
        cursor.execute("""
            DELETE FROM %s
            WHERE "%s" = %s
            """ % (self.table_name, self._id_name,
                adapt(self.data[self._id_column])))

    def refresh(self):
        self.update(self.get(self.data[self._id_column]))

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
        print result
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
