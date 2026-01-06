from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, text
import uuid
from app.config.base import Base


class ChatMessageSource(Base):
    __tablename__ = "chat_message_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_session_messages.id", ondelete="CASCADE"),
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(50),  # pdf | web | db | tool
        nullable=False,
    )

    source_name: Mapped[str] = mapped_column(String(255))

    chunk_id: Mapped[str | None] = mapped_column(String(255))

    source_metadata: Mapped[dict | None] = mapped_column(JSON)

    message: Mapped["ChatSessionMessages"] = relationship(
        "ChatSessionMessages",
        back_populates="sources",
    )
