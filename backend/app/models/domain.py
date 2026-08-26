from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from geoalchemy2 import Geography
from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from backend.app.db.session import Base

DATA_SOURCES_ID = "data_sources.id"
ASSETS_ID = "assets.id"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UUIDTimestampModel(Base):
    __abstract__ = True
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class Organization(UUIDTimestampModel):
    __tablename__ = "organizations"
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(2))
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)


class User(UUIDTimestampModel):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"), Index("ix_users_organization", "organization_id"))
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(32), default="member", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DataSource(UUIDTimestampModel):
    __tablename__ = "data_sources"
    __table_args__ = (Index("ix_data_sources_country_status", "country_code", "approval_status"),)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(2))
    source_url: Mapped[str | None] = mapped_column(Text)
    approval_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    commercial_use_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class Dataset(UUIDTimestampModel):
    __tablename__ = "datasets"
    __table_args__ = (UniqueConstraint("data_source_id", "external_id", name="uq_datasets_source_external"), Index("ix_datasets_data_source", "data_source_id"))
    data_source_id: Mapped[UUID] = mapped_column(ForeignKey(DATA_SOURCES_ID), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), default="1", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)


class IngestionRun(UUIDTimestampModel):
    __tablename__ = "ingestion_runs"
    __table_args__ = (Index("ix_ingestion_runs_source_started", "data_source_id", "started_at"), Index("ix_ingestion_runs_dataset", "dataset_id"))
    data_source_id: Mapped[UUID] = mapped_column(ForeignKey(DATA_SOURCES_ID), nullable=False)
    dataset_id: Mapped[UUID | None] = mapped_column(ForeignKey("datasets.id"))
    adapter_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="running", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_seen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_written: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)


class Address(UUIDTimestampModel):
    __tablename__ = "addresses"
    __table_args__ = (Index("ix_addresses_country_postcode", "country_code", "postal_code"),)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    formatted_address: Mapped[str | None] = mapped_column(Text)
    address_line_1: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))
    postal_code: Mapped[str | None] = mapped_column(String(32))
    location: Mapped[Any | None] = mapped_column(Geography("POINT", srid=4326))


class SourcedModel(UUIDTimestampModel):
    __abstract__ = True
    data_source_id: Mapped[UUID] = mapped_column(ForeignKey(DATA_SOURCES_ID), nullable=False)
    ingestion_run_id: Mapped[UUID | None] = mapped_column(ForeignKey("ingestion_runs.id"))
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class Asset(SourcedModel):
    __tablename__ = "assets"
    __table_args__ = (UniqueConstraint("data_source_id", "source_record_id", name="uq_assets_source_record"), Index("ix_assets_address", "address_id"))
    address_id: Mapped[UUID | None] = mapped_column(ForeignKey("addresses.id"))
    asset_type: Mapped[str | None] = mapped_column(String(64))
    area_sq_m: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    year_built: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)


class Transaction(SourcedModel):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("data_source_id", "source_record_id", name="uq_transactions_source_record"), Index("ix_transactions_asset_date", "asset_id", "transaction_date"))
    asset_id: Mapped[UUID | None] = mapped_column(ForeignKey(ASSETS_ID))
    transaction_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    currency: Mapped[str | None] = mapped_column(String(3))
    transaction_type: Mapped[str | None] = mapped_column(String(64))


class Listing(SourcedModel):
    __tablename__ = "listings"
    __table_args__ = (UniqueConstraint("data_source_id", "source_record_id", name="uq_listings_source_record"), Index("ix_listings_asset_status", "asset_id", "status"))
    asset_id: Mapped[UUID | None] = mapped_column(ForeignKey(ASSETS_ID))
    listed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    asking_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    currency: Mapped[str | None] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)


class MarketMetric(SourcedModel):
    __tablename__ = "market_metrics"
    __table_args__ = (UniqueConstraint("data_source_id", "source_record_id", name="uq_market_metrics_source_record"), Index("ix_market_metrics_geo_period", "country_code", "region", "period_start"))
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    region: Mapped[str | None] = mapped_column(String(120))
    metric_name: Mapped[str] = mapped_column(String(120), nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Signal(SourcedModel):
    __tablename__ = "signals"
    __table_args__ = (UniqueConstraint("data_source_id", "source_record_id", name="uq_signals_source_record"), Index("ix_signals_type_detected", "signal_type", "detected_at"))
    asset_id: Mapped[UUID | None] = mapped_column(ForeignKey(ASSETS_ID))
    signal_type: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_entity_created", "entity_type", "entity_id", "occurred_at"), Index("ix_audit_events_actor_occurred", "actor_type", "actor_id", "occurred_at"), Index("ix_audit_events_organization_occurred", "organization_id", "occurred_at"), Index("ix_audit_events_user_occurred", "user_id", "occurred_at"))
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    organization_id: Mapped[UUID | None] = mapped_column(ForeignKey("organizations.id"))
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    actor_type: Mapped[str] = mapped_column(String(32), default="system", nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    request_id: Mapped[str | None] = mapped_column(String(128))
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON)