import sqlalchemy as sa
import sqlalchemy.orm as orm
from .db_session import SqlAlchemyBase


class Stats(SqlAlchemyBase):
    __tablename__ = "stats"

    id = sa.Column(sa.Integer,
                   primary_key=True, autoincrement=True)
    user_id = sa.Column(
        sa.Integer, sa.ForeignKey("users.id")
    )
    server_id = sa.Column(
        sa.Integer, sa.ForeignKey("servers.id")
    )
    message_count = sa.Column(sa.Integer, nullable=True)

    user = orm.relationship("User")
    server = orm.relationship("Server")
