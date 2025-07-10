import os

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session

debug = False

SqlAlchemyBase = orm.declarative_base()
__factory = None


def global_init(db_url):
    global __factory

    if __factory:
        return

    if not db_url:
        raise Exception("Необходимо указать URL базы данных через аргумент")

    engine = sa.create_engine(db_url, echo=debug)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()
