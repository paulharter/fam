"""
This is just work in progress

Doesnt do anything right now
"""



import datetime


class FamMigration(object):

    timestamp = "2016-05-30T09:30:10Z"

    def up(self, db, doc):
        pass

    def down(self, db, doc):
        pass


def migrate(db, obj, migrations, ts=None):

    dst = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ") if ts is None else ts

    