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
    if not User.exists({'name': 'Derek'}):
        user = User.new({'name': 'Derek'})
        print user.id
        # 1
        del(user)
        user = User.get(1)
        user.email = 'derek@derekarnold.net'
        user.save()
        user.delete()
    print User.where({'name': 'Derek'})
    # Now there aren't any.
    
But that's not all!

    import candle

    class Vet(candle.Candle):
        table_name = 'vets'


    class Dog(candle.Candle):
        table_name = 'dogs'
        # no _id_name needed because "id" is the default.

        @classmethod
        def dogs_named_steve(cls):
            return cls.where({'name': 'steve'})

        @classmethod
        @defaultcommit
        def put_hats_on_dogs_named_steve(cls):
            """Use normal psycopg2 syntax here. @defaultcommit decorator commits
            the transaction once the method is done executing. Otherwise,
            self.commit will do the trick."""
            cursor = self.cursor()
            cursor.execute("""
                UPDATE "%s" SET hat_status = TRUE
                WHERE "name" = 'steve'
                """ % cls.table_name)
            return True

        @property
        def vet(self):
            """This would normally be done via Vet::get(), but here's how you
            can return another class's instance."""
            cursor = self.cursor()
            cursor.execute("""
                SELECT * FROM vets
                WHERE id = %s
                """, [self.vet_id])
            return Vet(cursor.fetchone()) # The constructor will take any dict,
                                          # Filtering columns that are not in
                                          # the table.

And lastly, because we're using PostgreSQL and not some [second rate database](http://mysql.org),
we have access to powerful user-defined database functions. Candle supports these transparently:

Define this (basically useless) function:

    CREATE OR REPLACE FUNCTION test_function(dogname varchar) RETURNS SETOF dogs AS $q$
        BEGIN
            RETURN QUERY SELECT * FROM dogs WHERE name = $1;
            RETURN;
        END;
    $q$ LANGUAGE PLPGSQL IMMUTABLE;

You can then do the following:

    dog = Dog.test_function('steve')

If a column name exists with the same name, it takes precedence. No database-side
type checking is performed for the result, but this might change in the future
since this information is exposed in `pg_catalog.pg_proc`.