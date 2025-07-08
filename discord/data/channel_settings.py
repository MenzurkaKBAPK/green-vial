import sqlalchemy as sa
import sqlalchemy.orm as orm
from .db_session import SqlAlchemyBase


class ChannelSettings(SqlAlchemyBase):
    __tablename__ = "channel_settings"

    id = sa.Column(sa.Integer,
                   primary_key=True, autoincrement=True)
    user_id = sa.Column(
        sa.Integer, sa.ForeignKey("users.id")
    )
    server_id = sa.Column(
        sa.Integer, sa.ForeignKey("servers.id")
    )
    name = sa.Column(sa.String, nullable=True)
    permissions = sa.Column(sa.String, nullable=True)

    user = orm.relationship("User")
    server = orm.relationship("Server")
