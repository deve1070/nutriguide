from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.user import User




class BotUser(Base):
    __tablename__ = "bot_users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    bot_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="bot_users")

    def __repr__(self) -> str:
        return f"<BotUser id={self.id} bot_name={self.bot_name} user_id={self.user_id}>"

