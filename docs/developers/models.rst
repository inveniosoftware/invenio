.. _developers-models:

Models
======

Models define a Python-ic interface to relational databases using the
`SQLAlchemy`_ toolkit that *provides a full suite of well
known enterprise-level persistence patterns, designed for efficient and
high-performing database access, adapted into a simple and Pythonic domain
language* [SQLAlchemy2013]_.

In order to add SQLAlchemy support to our application, the
`Flask-SQLAlchemy`_ extension is used.  It provides useful defaults as
well as extra declarative base helpers.  We recommend reading
`Official Tutorial` for a full introduction and `Other Tutorial` for
better understanding of ORM concepts.


Code structure
--------------

Our custom bridge contains several custom types and driver hacks for
smoother integration with multiple database engines. The code structure
follows::

    invenio/ext/sqlalchemy
        /engines
            mysql.py
        __init__.py
        expressions.py
        types.py
        utils.py


Before you start writing a new model please take a look at the
:obj:`~invenio.ext.sqlalchemy.db` object.  It will also make it easier to
understand the following example of a simple model written using SQLAlchemy::

    # General imports.
    from invenio.ext.sqlalchemy import db

    # Create your models here.


    class User(db.Model):
        """Represents a User record."""
        __tablename__ = 'user'
        id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                       autoincrement=True)
        email = db.Column(db.String(255), nullable=False, server_default='',
                          index=True)
        _password = db.Column(db.LargeBinary, name="password",
                              nullable=False)
        note = db.Column(db.String(255), nullable=True)
        settings = db.Column(db.MutableDict.as_mutable(db.MarshalBinary(
            default_value=lambda: dict(), force_type=dict)),
            nullable=True)
        nickname = db.Column(db.String(255), nullable=False, server_default='',
                             index=True)
        last_login = db.Column(db.DateTime, nullable=True)


All your models used in a module have to be located in ``models.py`` inside
your module package (see :ref:`developers-modules` for developers).

.. note:: If you have any relations between tables use ``ForeignKey``
    definitions and `SQLAlchemy Relationships`_.


Quering
-------

Once you have written models it is possible to change the old way of writing
SQL queries::

    >>> run_sql("SELECT user.nickname FROM user")
    [u.nickname for u in User.query.all()]
    # Old Invenio way ...
    >>> User.query.values(User.nickname)
    >>> db.session.query(User.nickname).all()
    >>> db.select([User.nickname]).execute().fetchall()
    # All roads lead to Rome ... however some are slower.


We also need a WHERE clause in our SQL statements. Let's prepare a statement for
a list with all messages sent by a user::

    >>> db.select([User.nickname, MsgMESSAGE.subject]).execute().fetchall()
    [('admin', 'test1'),
     ('admin', 'test2'),
     ('jekyll', 'test1'),
     ('jekyll', 'test2'),
     ...
     ('balthasar', 'test1'),
     ('balthasar', 'test2')]

    # Something is missing in our query ...
    >>> db.select([User.nickname, MsgMESSAGE.subject], User.id==MsgMESSAGE.id_user_from).execute().fetchall()
    [('admin', 'test1'),
     ('admin', 'test2')]
    # This is much better.

Operators:

- ``&``, ``and_`` (redefined because of Python operator priorites)
- ``|``, ``or_``
- ``~``, ``not_``
- ``==``, ``<=``, ``=>``, ``<``, ``>``
- ``func.like``
- text operator ``+``::

    >>> str(MsgMESSAGE.subject + ': ' + MsgMESSAGE.body)
    '"msgMESSAGE".subject || :subject_1 || "msgMESSAGE".body'
    # :subject_1 will be replaced by ': ' during query execution


Let's use ORM for getting messages sent by "admin"::

    >>> admin = User.query.filter(User.nickname.like('admin')).one()
    >>> admin
    admin <root@localhost>
    >>> admin.sent_messages
    [From: admin<root@localhost>, Subject: <test1> body1,
     From: admin<root@localhost>, Subject: <test2> body2]
    >>> User.query.filter(User.nickname.like('%a%'))
    [admin <root@localhost>,
     dorian <dorian.gray@cds.cern.ch>,
     balthasar <balthasar.montague@cds.cern.ch>


Which brings us to another example where we create ''reusable'' queries
using `db.bindparam` instead of an actual filter value::

    >>> q = User.query.filter(User.nickname.like(db.bindparam('nickname')))
    >>> q.params({'nickname':'admin'}).one()
    admin <root@localhost>
    >>> q.params({'nickname':'%a%'}).all()
    [admin <root@localhost>,
     dorian <dorian.gray@cds.cern.ch>,
     balthasar <balthasar.montague@cds.cern.ch>]


Subqueries
----------

Let's start with simple example::

    >>> s = db.session.query(User.id).filter(User.nickname.like("%a%")).subquery()
    >>> MsgMESSAGE.query.filter(MsgMESSAGE.id_user_from.in_(s)).all()

You can combine subqueries with the delete statement::

    >>> sub = db.session.query(UserMsgMESSAGE.id_user_to, UserMsgMESSAGE.id_msgMESSAGE).outerjoin(User, User.id==UserMsgMESSAGE.id_user_to).outerjoin(MsgMESSAGE, UserMsgMESSAGE.id_msgMESSAGE==MsgMESSAGE.id).filter(db.or_(User.id==None, MsgMESSAGE.id==None)).all()
    # Find links to not existing messages or users.
    >>> db.session.query(UserMsgMESSAGE).filter(db.tuple_(UserMsgMESSAGE.id_user_to, UserMsgMESSAGE.id_msgMESSAGE).in_(sub)).delete(synchronize_session=False)
    # Delete messages found in subquery.

Schema
------

When you load all models, you want it to be easy to print create table
statements for these models::

    >>> for table in db.metadata.tables.values(): print CreateTable(table, on=db.engine.name, bind=db.engine)


Similarly, we can print relevant create statements for indexes::

    >>> [str(CreateIndex(i, on=db.engine.name, bind=db.engine)) for i in table.indexes for table in db.metadata.tables.values() if hasattr(table, 'indexes')]


Improve code readability
------------------------

Queries and filters can get quite long and some parts are unnecessarily
copied many times.

Some examples follow::

    reminder_status = CFG_WEBMESSAGE_STATUS_CODE['REMINDER']

    db.session.query(UserMsgMESSAGE).join(User, MsgMESSAGE).filter(db.not_(AsBINARY(UserMsgMESSAGE.status.__eq__(reminder_status)))  & (UserMsgMESSAGE.id_user_to == 1)).all() 

    db.session.query(UserMsgMESSAGE).join(User).filter(
        (User.id == MsgMESSAGE.id_user_from) & (UserMsgMESSAGE.id_msgMESSAGE == MsgMESSAGE.id) &
        db.not_(AsBINARY(UserMsgMESSAGE.status.__eq__(reminder_status)))  & (UserMsgMESSAGE.id_user_to == 1)).all()

    filter_all_message_from_user = lambda uid, status: (User.id == MsgMESSAGE.id_user_from) & (UserMsgMESSAGE.id_msgMESSAGE == MsgMESSAGE.id) & db.not_(AsBINARY(UserMsgMESSAGE.status.__eq__(status)))  & (UserMsgMESSAGE.id_user_to == uid)



.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _SQLAlchemy Relationships: http://docs.sqlalchemy.org/en/latest/orm/extensions/declarative.html#configuring-relationships
.. _Flask-SQLAlchemy: http://pythonhosted.org/Flask-SQLAlchemy/
.. _Official Tutorial: http://docs.sqlalchemy.org/en/latest/orm/tutorial.html
.. _Other Tutorial: http://www.rmunn.com/sqlalchemy-tutorial/tutorial.html

.. [SQLAlchemy2013] SQLAlchemy website: http://www.sqlalchemy.org/
