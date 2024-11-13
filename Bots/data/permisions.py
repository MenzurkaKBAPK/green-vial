import sqlalchemy as sa
import sqlalchemy.orm as orm

from config import PERMISSION_LEVELS

from .db_session import SqlAlchemyBase


class UserPermissions(SqlAlchemyBase):
    __tablename__ = "permissions"

    id = sa.Column(sa.Integer,
                   primary_key=True, autoincrement=True)

    user_id = sa.Column(
        sa.Integer, sa.ForeignKey("users.id"), unique=True
    )
    permission_level = sa.Column(sa.Integer)

    user = orm.relationship("User")

    def __repr__(self):
        return (
            f"<UserPermission> [{self.user_id}] {self.permission_level} -> "
            f"{PERMISSION_LEVELS[self.permission_level][0]}]"
        )
