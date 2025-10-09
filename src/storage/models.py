from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    patterns: Mapped[list["Pattern"]] = relationship(back_populates="service", cascade="all, delete-orphan")
    policies: Mapped[list["Policy"]] = relationship(back_populates="service", cascade="all, delete-orphan")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="service", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Service(id={self.id}, name={self.name}, team_id={self.team_id})>"


class Pattern(Base):
    __tablename__ = "patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    signature: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    representative_message: Mapped[str] = mapped_column(Text, nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0)
    sampled_count: Mapped[int] = mapped_column(Integer, default=0)
    first_seen: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    severity_distribution: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    service: Mapped["Service"] = relationship(back_populates="patterns")

    def __repr__(self) -> str:
        return f"<Pattern(id={self.id}, signature={self.signature[:8]}..., count={self.count})>"


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    global_rate: Mapped[float] = mapped_column(Float, default=1.0)
    severity_rates: Mapped[dict] = mapped_column(JSON, nullable=False)
    pattern_rates: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    anomaly_boost: Mapped[float] = mapped_column(Float, default=2.0)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(50), nullable=False)  # 'llm' or 'rule-based'
    llm_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    service: Mapped["Service"] = relationship(back_populates="policies")

    def __repr__(self) -> str:
        return f"<Policy(id={self.id}, service_id={self.service_id}, version={self.version}, active={self.is_active})>"


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # 'running', 'completed', 'failed'
    logs_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    patterns_found: Mapped[int] = mapped_column(Integer, default=0)
    anomalies_detected: Mapped[int] = mapped_column(Integer, default=0)
    policy_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    run_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    service: Mapped["Service"] = relationship(back_populates="analysis_runs")

    def __repr__(self) -> str:
        return f"<AnalysisRun(id={self.id}, service_id={self.service_id}, status={self.status})>"
