import sqlalchemy as sa
from .db_session import SqlAlchemyBase


class Phrase(SqlAlchemyBase):
    __tablename__ = "phrases"

    id = sa.Column(sa.Integer,
                   primary_key=True, autoincrement=True)
    phrase = sa.Column(
        sa.String, nullable=True
    )
