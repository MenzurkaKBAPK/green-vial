import sqlalchemy as sa
import sqlalchemy.orm as orm
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = "users"

    id = sa.Column(sa.Integer,
                   primary_key=True, autoincrement=True)
    user_id = sa.Column(
        sa.String, nullable=True
    )

    stats = orm.relationship("Stats", back_populates="user")
    delayed_messages = orm.relationship(
        "DelayedMessage", back_populates="user")
