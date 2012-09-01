Candle
------


PostgreSQL database class. The staticmethods are your model, the instances are
your rows. Same philosphy as [paraffin](http://github.com/lysol/paraffin), but
better because it's Python.

Usage:

    import candle

    class User(candle.Candle):
        _id_name = 'id'
        table_name = 'users'

    User.set_conn("dbname=testcandle user=testcandle host=localhost")
    print User.get(1)
    User.delete(1)

More to come!