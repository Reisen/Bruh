"""
    The code is really bad, but this provides a very simple ORM that allows
    access to the database. It provides a simple query language, and a mapper.
    This code is extremely bad, but it was a fun thing to play with writing.
    Also the code is REALLY bad.

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

class Column(object):
    """
    All attributes of mapped classes are instances of a Column. The Column
    is used when mapping attributes and classes.
    """
    def __init__(self):
        self.primary_key = False


# Expressions; These are used in querying the database.
class BinaryExpression(object):
    """
    BinaryExpressions are created when a Column is compared against a value.
    The column, the value, and the comparison type are stored within this
    object.
    """
    def __init__(self, column, value, operator):
        self.column   = column
        self.value    = value
        self.operator = operator


class or_(object):
    """Create an OR Expression"""
    def __init__(self, *expressions):
        self.expressions = expressions


# Column Types
class Integer(Column):
    typename = 'INTEGER'
    
    def __init__(self, primary_key = False):
        self.primary_key = primary_key

    def __eq__(self, num):
        return BinaryExpression(self, num, '=')

    def __lt__(self, num):
        return BinaryExpression(self, num, '<')

    def __gt__(self, num):
        return BinaryExpression(self, num, '>')


class String(Column):
    typename = 'VARCHAR'
    def __eq__(self, s):
        return BinaryExpression(self, s, '=')


class Query(object):
    """
    This class is responsible for handling a connection to the database, and
    also provides the interface to it.
    """
    def __init__(self, connection):
        self.connection = connection


    def query_to_object(self, cursor, rows):
        results = []

        # Luckily, sqlite3 allows an easy way of finding out which column is
        # which value, so we just look at cursor.description, and map to the
        # right attributes this way.
        for row in rows:
            # If there is a map target, we fill in the attributes on this
            # mappable class.
            if self.map_target is not None:
                o = self.map_target()
                for i, c in enumerate(cursor.description):
                    setattr(o, c[0], row[i])

                # We also attach a method to the class so that .save() will save
                # the information to the database if the class has been modified.
                def save_object():
                    update_query = 'UPDATE %s SET\n' % o.__class__.table
                    extra_subs = []
                    for attribute in o.__dict__:
                        if attribute not in o.__class__.__dict__:
                            continue

                        if isinstance(getattr(o.__class__, attribute), Column):
                            update_query += '\t%s = ?,\n' % getattr(o.__class__, attribute).name
                            extra_subs.append(getattr(o, attribute))

                    update_query = update_query[:-2] + '\nWHERE id = ?'
                    extra_subs.append(getattr(o, 'id'))
                    self.connection.execute(update_query, tuple(extra_subs))
                
                # Attach our newly created closure for this query to the object
                # being returned. Each object will have It's own closure with a
                # query for updating it.
                o.save = save_object

                results.append(o)

            # If there is no map target, then we just return a tuple of values
            # requested directly from sqlite3.
            else:
                results.append(row)

        return results

    def all(self):
        cur = self.connection.execute(repr(self), tuple(self.substitutions))
        return self.query_to_object(cur, cur.fetchall())

    def one(self):
        cur = self.connection.execute(repr(self), tuple(self.substitutions))
        obj = cur.fetchone()

        if obj is None:
            return None

        return self.query_to_object(cur, [obj])[0]

    def desc(self, o):
        if isinstance(o, Column):
            self.order_clause = ' ORDER BY %s DESC ' % o.name
            return self

        self.order_clause = ' ORDER BY %s DESC ' % o
        return self

    def asc(self, o):
        if isinstance(o, Column):
            self.order_clause = ' ORDER BY %s ASC ' % o.name
            return self

        self.order_clause = ' ORDER BY %s ASC ' % o
        return self

    def query(self, *args):
        # Instead of placing values directly into a query, we store them in a
        # dictionary. These are passed to sqlite to fill in ? replacement
        # values giving us quick and easy SQL injection protection.
        self.substitutions = []

        self.query_string = 'SELECT '
        self.from_string  = ' FROM '
        self.where_clause = ''
        self.limit_clause = ''
        self.order_clause = ''
        self.map_target = None

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
            # from that table (*). This should also be the target that all the
            # attributes returned from the db should be mapped to.
            elif 'table' in arg.__dict__:
                if arg.table not in self.from_string:
                    self.from_string += arg.table + ', '

                self.query_string += arg.table + '.*, '
                self.map_target = arg

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
                             +  ' ' + arg.operator + ' ' \
                             + arg.value.parent.table + '.' + arg.value.name

            # If it is not another Column, but a value, we cannot just
            # insert blindly without worrying about injections, instead we
            # use SQLite's question mark substitution.
            else:
                self.substitutions.append(arg.value)
                where_clause += arg.column.parent.table + '.' + arg.column.name + (' %s ?' % arg.operator)

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
        return self.query_string + self.from_string + self.where_clause + self.order_clause + self.limit_clause


class Connection(object):
    """
    This class is responsible for handling database connections, and for
    mapping objects.
    """
    def __init__(self, irc):
        self.connection = sqlite3.connect('./data/' + irc.server + '.db', detect_types = sqlite3.PARSE_COLNAMES)

    def map(self, mapper):
        """
        Inspect a class, and prepare it so that it is usable in queries and
        query mapping. If the class doesn't exist in the database, build a
        create query and set it up.
        
        """
        # Set the name for the table stored in the database engine. This is
        # used when generating queries.
        table_name = 'tbl_' + mapper.__name__

        # sqlite's table_info pragma returns no information if the table
        # doesn't exist, so we should create it.
        table = self.connection.execute('PRAGMA table_info({})'.format(table_name)).fetchall()
        create_query = ''
        if len(table) == 0:
            create_query = 'CREATE TABLE {} (\n'.format(table_name)

        else:
            # The table already exists, if the class is also already mapped
            # then there's no reason to remap. The logic here really should
            # be rewritten, one day I'll do it.
            if 'table' in mapper.__dict__:
                return

        mapper.table = table_name

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

        # If a create query was made, execute it. This code is so poorly
        # thought out it's horrible.
        if len(create_query) > 0:
            create_query = create_query[:-2] + '\n);'
            print(create_query)
            self.connection.execute(create_query).close()

    def add(self, o):
        # If the id attribute is not a Column instance (meaning it has been
        # assigned to something), then this column is already mapped to
        # something in the database, and we should not add it again.
        if not isinstance(o.id, Column):
            return

        insert_query = 'INSERT INTO %s (' % o.table
        extra_subs = []
        for attribute in o.__class__.__dict__:
            if isinstance(getattr(o.__class__, attribute), Column):
                insert_query += getattr(o.__class__, attribute).name + ', '

        insert_query = insert_query[:-2] + ') VALUES ('
        for attribute in o.__class__.__dict__:
            if attribute == 'id':
                insert_query += 'NULL, '

            elif isinstance(getattr(o.__class__, attribute), Column):
                insert_query += '?, '
                extra_subs.append(getattr(o, attribute))

        insert_query = insert_query[:-2] + ');'
        self.connection.execute(insert_query, tuple(extra_subs))
        self.connection.commit()

        # We need to re-query the database to get the newly assigned ID for the
        # instance.
        new_id, = self.connection.execute('SELECT id FROM %s ORDER BY id DESC LIMIT 1' % o.table).fetchone()
        o.id = new_id

        # We should also add a new method that allows .save() calls on this new
        # mapped object.
        def save_object():
            update_query = 'UPDATE %s SET\n' % o.__class__.table
            extra_subs = []
            for attribute in o.__dict__:
                if attribute not in o.__class__.__dict__:
                    continue

                if isinstance(getattr(o.__class__, attribute), Column):
                    update_query += '\t%s = ?,\n' % getattr(o.__class__, attribute).name
                    extra_subs.append(getattr(o, attribute))

            update_query = update_query[:-2] + '\nWHERE id = ?'
            extra_subs.append(getattr(o, 'id'))
            self.connection.execute(update_query, tuple(extra_subs))
        
        o.save = save_object

    def query(self, *args):
        q = Query(self.connection)
        return q.query(*args)


class User(object):
    id   = Integer(primary_key = True)
    name = String()

    def __init__(self, name = None):
        self.name = name


@event('BRUH')
def database(irc):
    irc.db = Connection(irc)
    print(irc.db)
