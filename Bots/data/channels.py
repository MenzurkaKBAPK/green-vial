import sqlalchemy as sa
import sqlalchemy.orm as orm
from .db_session import SqlAlchemyBase


class Channels(SqlAlchemyBase):
    __tablename__ = "channels"

    id = sa.Column(sa.Integer,
                   primary_key=True, autoincrement=True)
    server_id = sa.Column(
        sa.Integer, sa.ForeignKey("servers.id")
    )
    channel_id = sa.Column(sa.Integer, nullable=True)
    channel_type = sa.Column(sa.Integer, nullable=True)

    server = orm.relationship("Server")
