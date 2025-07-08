import sqlalchemy as sa
import sqlalchemy.orm as orm
from .db_session import SqlAlchemyBase


class Server(SqlAlchemyBase):
    __tablename__ = "servers"

    id = sa.Column(sa.Integer,
                   primary_key=True, autoincrement=True)
    server_id = sa.Column(
        sa.String, nullable=True
    )

    stats = orm.relationship("Stats", back_populates="server")
