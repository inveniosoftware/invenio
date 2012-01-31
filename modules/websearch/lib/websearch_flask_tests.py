from flask import current_app, request
from invenio.sqlalchemyutils import db
from flask import session, g

from invenio.testutils import make_flask_test_suite, run_test_suite, \
                              FlaskSQLAlchemyTest

from fixture import SQLAlchemyFixture
from invenio.webaccount_fixtures import UserData, UsergroupData, \
                                        UserUsergroupData
from invenio.websession_model import User, Usergroup, UserUsergroup

from invenio.websearch_model import Collection, CollectionCollection, \
    Externalcollection
from invenio.websearch_fixtures import CollectionData, \
    CollectionCollectionData, \
    ExternalcollectionData

fixture = SQLAlchemyFixture(
        env={'UserData': User, 'UsergroupData': Usergroup,
             'UserUsergroupData': UserUsergroup,
             'CollectionData': Collection,
             'ExternalcollectionData': Externalcollection,
             'CollectionCollectionData': CollectionCollection},
        engine=db.metadata.bind,
        session=db.session
        )

def p(c, level=0):
    if c:
        print ' '*level, '- ',c.name
        for i in c.collection_children_r:
            p(i, level+1)


class WebSearchCollectionTest(FlaskSQLAlchemyTest):

    @fixture.with_data(UserData, ExternalcollectionData, CollectionData, CollectionCollectionData)
    def test_loading_collection_tree(data, self):
        users = data.UserData
        collections = data.CollectionData
        p(Collection.query.order_by(Collection.id).first())

        print
        for c in Collection.query.all():
            print dict(c)
            print c.names

        print len(dict(data.CollectionCollectionData))


    @fixture.with_data(ExternalcollectionData, CollectionData)
    def test_external_collection(data, self):
        print
        print '----# EXTERNAL COLLECTIONS ----'
        for c in Collection.query.all():
            print c.name, ': ',
            print len([a for a in c._externalcollections])
        print '-------------------------------'
        print 'Total: ', sum(map(len, [c._externalcollections for c in Collection.query.all()]))



TEST_SUITE = make_flask_test_suite(WebSearchCollectionTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)

