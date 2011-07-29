"""
    Provides a very simple ORM that allows access to the database. It provides
    a simple query language, and a mapper. This code is extremely bad, but it
    was a fun thing to play with writing.

    Instructions
    ------------

    To use the mapper, you must first define a class to be mapped. To do this
    you simply create a class with column types as attributes, for example:

        class User(object):
            id      = Integer(primary_key = True)
            msgs    = Integer()
            nick    = String()

    To use this class, it needs to be mapped. Any connection object can map a
    class (this doesn't mean it has to be mapped in EVERY connection, it only
    has to be mapped once).

        c = Connection(irc)
        c.map(User)

    The mapper will automatically create a table for the User class if one does
    not already exist. Querying the database is simple, and works like this:

        >>> repr(c.query(User))
        SELECT tbl_User.* FROM tbl_User

        >>> repr(c.query(User.id, User.nick))
        SELECT tbl_User.id, tbl_User.nick FROM tbl_User

        >>> repr(c.query(User).where(User.nick == 'Reisen'))
        SELECT tbl_User.* FROM tbl_User WHERE tbl_User.nick = ?

        >>> repr(c.query(User).where(or_(
        ...     User.nick == 'Reisen',
        ...     User.nick == 'John',
        ...     User.id   == 1
        ... ))


    This produces

"""

import sqlite3
from plugins.bruh import event

# Define column types for the mapper.
class Column(object):
    def __init__(self):
        self.primary_key = False


# Define Expression types, these are used by the query language to construct
# where clauses from expressions involving columns.
class BinaryExpression(object):
    def __init__(self, column, value):
        self.column = column
        self.value  = value


class or_(object):
    """Create an OR Expression"""
    def __init__(self, *expressions):
        self.expressions = expressions


class Integer(Column):
    typename = 'INTEGER'
    
    def __init__(self, primary_key = False):
        self.primary_key = primary_key

    def __eq__(self, num):
        return BinaryExpression(self, num)


class String(Column):
    typename = 'VARCHAR'
    def __eq__(self, s):
        return BinaryExpression(self, s)


class Query(object):
    """
    This class is responsible for handling a connection to the database, and
    also provides the interface to it.
    """
    def __init__(self, connection):
        self.connection = connection

    def query(self, *args):
        # Instead of placing values directly into a query, we store them in a
        # dictionary. These are passed to sqlite to fill in ? replacement
        # values giving us quick and easy SQL injection protection.
        self.substitutions = []

        self.query_string = 'SELECT '
        self.from_string  = ' FROM '
        self.where_clause = ''

        # Query takes a number of different arguments, and turns them into
        # a valid select/from query.
        for arg in args:
            # Mapped Columns select a specific column from the table that they
            # are associated with in the map() call.
            if isinstance(arg, Column):
                if arg.parent.table not in self.from_string:
                    self.from_string += arg.parent.table + ', '
                
                self.query_string += arg.parent.table + '.' + arg.name + ', '

            # If an entire mapped class is pased, we should select everything
            # from that table (*).
            elif 'table' in arg.__dict__:
                if arg.table not in self.from_string:
                    self.from_string += arg.table + ', '

                self.query_string += arg.table + '.*, '

        # Remove end commas from SELECT and FROM parts.
        self.query_string = self.query_string[:-2]
        self.from_string  = self.from_string[:-2]
        return self

    def where_build(self, arg):
        """Build a WHERE condition based on the type of arg received."""

        # BinaryExpressions are created from comparing a Column to a value
        # or another Column, I.E, Class.id == 1.
        where_clause = ''
        if isinstance(arg, BinaryExpression):
            # The second operand may be a value, or another Column. 
            if isinstance(arg.value, Column):
                where_clause += arg.column.parent.table + '.' + arg.column.name \
                             +  ' = ' \
                             + arg.value.parent.table + '.' + arg.value.name

            # If it is not another Column, but a value, we cannot just
            # insert blindly without worrying about injections, instead we
            # use SQLite's question mark substitution.
            else:
                self.substitutions.append(arg.value)
                where_clause += arg.column.parent.table + '.' + arg.column.name + ' = ?'

        elif isinstance(arg, or_):
            where_clause = '('
            for expression in arg.expressions:
                where_clause += self.where_build(expression) + ' OR '

            where_clause = where_clause[:-4] + ')'

        return where_clause

    def where(self, *args):
        if len(self.where_clause) == 0:
            self.where_clause = ' WHERE '
        else:
            self.where_clause += ' AND '

        # Arguments may be a variety of conditions, from BinaryExpressions to
        # more complex SQL conditions like 'LIKE' clauses. Here we determine
        # what type of clause we're dealing with, and use it in the query.
        for arg in args:
            self.where_clause += self.where_build(arg) + ' AND '

        # Remove the trailing 'AND' from the query.
        self.where_clause = self.where_clause[:-5]
        return self

    def __repr__(self):
        return self.query_string + self.from_string + self.where_clause


class Connection(object):
    """
    This class is responsible for handling database connections, and for
    mapping objects.
    """
    def __init__(self, irc):
        self.connection = sqlite3.connect('./data/' + irc.server)

    def map(self, mapper):
        """
        Inspect a class, and prepare it so that it is usable in queries and
        query mapping. If the class doesn't exist in the database, build a
        create query and set it up.
        
        """
        # Set the name for the table stored in the database engine. This is
        # used when generating queries.
        mapper.table = 'tbl_' + mapper.__name__

        # sqlite's table_info pragma returns no information if the table
        # doesn't exist, so we should create it.
        table = self.connection.execute('PRAGMA table_info({})'.format(mapper.table)).fetchall()
        create_query = ''
        if len(table) == 0:
            create_query = 'CREATE TABLE {} (\n'.format(mapper.table)

        # For each Column found in the class. We look up the string name of its
        # class attribute, and store it in the Column itself. This allows
        # introspection when mapping to a class, or when creating a table from
        # a class.
        for attr in mapper.__dict__:
            val = getattr(mapper, attr)
            if isinstance(val, Column):
                val.name = attr
                val.parent = mapper

                if len(create_query) > 0:
                    create_query += '\t{} {}'.format(val.name, val.typename)

                    if val.primary_key:
                        create_query += ' PRIMARY KEY'

                    create_query += ',\n'

        if len(create_query) > 0:
            create_query = create_query[:-2] + '\n);'
            print(create_query)
            self.connection.execute(create_query).close()

    def query(self, *args):
        q = Query(self.connection)
        return q.query(*args)


class User(object):
    id   = Integer(primary_key = True)
    name = String()


class E(object):
    pass
e = E()
e.server = 'test.db'
c = Connection(e)
c.map(User)


@event('BRUH')
def database(irc):
    irc.db = Connection(irc)
    irc.db.map(User)




    irc.db.query(User.name).all()
