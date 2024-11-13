import sqlalchemy as sa
import sqlalchemy.orm as orm
from .db_session import SqlAlchemyBase


class DelayedMessage(SqlAlchemyBase):
    __tablename__ = "delayed_messages"

    id = sa.Column(sa.Integer,
                   primary_key=True, autoincrement=True)

    from_user_id = sa.Column(
        sa.Integer, sa.ForeignKey("users.id")
    )
    to_user_id = sa.Column(sa.Integer)  # почему не работает ForeignKey

    message = sa.Column(sa.String)

    day = sa.Column(sa.Integer)
    month = sa.Column(sa.Integer)
    year = sa.Column(sa.Integer)
    hour = sa.Column(sa.Integer)
    minute = sa.Column(sa.Integer)

    user = orm.relationship("User")

    def __repr__(self):
        return (
            f"<DelayedMessage> [{self.day}.{self.month}.{self.year} "
            f"{self.hour}:{self.minute}] [{self.from_user_id} -> "
            f"{self.to_user_id}] {self.message}"
        )
