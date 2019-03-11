
from __future__ import absolute_import, division, print_function

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
from rmexp import config

engine = create_engine(config.DB_URI)


def get_session():
    Session = sessionmaker()
    Session.configure(bind=engine)
    session = Session()
    return session


class Connector(object):
    def __init__(self):
        self._engine = None
        return super(Connector, self).__init__()


class MYSQLConnector(object):
    def __init__(self):
        return super(MYSQLConnector, self).__init__()


def main():
    import sqlalchemy as db
    engine = db.create_engine('dialect+driver://user:pass@host:port/db')


if __name__ == '__main__':
    main()
