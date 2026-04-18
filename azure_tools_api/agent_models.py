from datetime import datetime
from typing import TYPE_CHECKING

# Try to import SQLAlchemy symbols. If imports fail (incompatible SQLAlchemy
# version or missing deps), fall back to lightweight stubs so this module can
# still be imported at runtime by code paths that don't need the ORM model.
try:
    from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
    from sqlalchemy.orm import Mapped, mapped_column
    _SA_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    _SA_AVAILABLE = False

    # Lightweight stubs to allow module import without SQLAlchemy.
    def mapped_column(*args, **kwargs):
        return None

    class Mapped:  # type: ignore[misc]
        pass

# Import Base from app.db if possible. If that import fails, provide a stub
# base class so the AzureAgentRecord class can still be defined.
if TYPE_CHECKING:
    # For type checkers, import the real Base
    from app.db import Base  # type: ignore
else:
    try:
        from app.db import Base  # type: ignore
    except Exception:  # pragma: no cover - environment dependent
        Base = type("StubBase", (), {})


class AzureAgentRecord(Base):
    __tablename__ = "azure_agent_records"
    __table_args__ = (UniqueConstraint("seller_id", name="uq_azure_agent_records_seller_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    agent_id: Mapped[str] = mapped_column(String(255), index=True)
    agent_name: Mapped[str] = mapped_column(String(255), index=True)
    agent_version: Mapped[str] = mapped_column(String(80))
    agent_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    instructions: Mapped[str] = mapped_column(String(4000))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
