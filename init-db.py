#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

# init-db.py

from sqlalchemy import create_engine, MetaData

from pakreq.db import USER, REQUEST
from pakreq.settings import BASE_DIR, get_config

DB_LINK = "sqlite:///{location}"

CONFIG_PATH = BASE_DIR / 'config' / 'pakreq.yaml'
CONFIG = get_config(['-c', CONFIG_PATH.as_posix()])

DB_URL = DB_LINK.format(location=CONFIG['db']['location'])

db_engine = create_engine(DB_URL)


def create_tables(engine=db_engine):
    """Create the tables"""
    meta = MetaData()
    meta.create_all(bind=engine, tables=[USER, REQUEST])


def drop_tables(engine=db_engine):
    """Delete the tables"""
    meta = MetaData()
    meta.drop_all(bind=engine, tables=[USER, REQUEST])


if __name__ == '__main__':
    create_tables(engine=db_engine)
