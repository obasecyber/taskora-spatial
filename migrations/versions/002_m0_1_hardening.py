"""Harden audit events and add supporting indexes."""

from alembic import op

revision = "002_m0_1_hardening"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE audit_events ADD COLUMN IF NOT EXISTS occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()")
    op.execute("ALTER TABLE audit_events ADD COLUMN IF NOT EXISTS actor_type VARCHAR(32) NOT NULL DEFAULT 'system'")
    op.execute("ALTER TABLE audit_events ADD COLUMN IF NOT EXISTS actor_id UUID")
    op.execute("ALTER TABLE audit_events ADD COLUMN IF NOT EXISTS request_id VARCHAR(128)")
    op.execute("ALTER TABLE audit_events DROP COLUMN IF EXISTS updated_at")
    op.execute("DROP INDEX IF EXISTS ix_audit_events_entity_created")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_entity_created ON audit_events (entity_type, entity_id, occurred_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_actor_occurred ON audit_events (actor_type, actor_id, occurred_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_organization ON users (organization_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_datasets_data_source ON datasets (data_source_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ingestion_runs_dataset ON ingestion_runs (dataset_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_organization_occurred ON audit_events (organization_id, occurred_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_user_occurred ON audit_events (user_id, occurred_at)")
    op.execute("""
        CREATE OR REPLACE FUNCTION reject_audit_event_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'audit_events are append-only';
        END;
        $$
    """)
    op.execute("DROP TRIGGER IF EXISTS audit_events_append_only ON audit_events")
    op.execute("CREATE TRIGGER audit_events_append_only BEFORE UPDATE OR DELETE ON audit_events FOR EACH ROW EXECUTE FUNCTION reject_audit_event_mutation()")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_audit_events_actor_occurred")
    op.execute("DROP INDEX IF EXISTS ix_audit_events_entity_created")
    op.execute("DROP INDEX IF EXISTS ix_users_organization")
    op.execute("DROP INDEX IF EXISTS ix_datasets_data_source")
    op.execute("DROP INDEX IF EXISTS ix_ingestion_runs_dataset")
    op.execute("DROP INDEX IF EXISTS ix_audit_events_organization_occurred")
    op.execute("DROP INDEX IF EXISTS ix_audit_events_user_occurred")
    op.execute("DROP TRIGGER IF EXISTS audit_events_append_only ON audit_events")
    op.execute("DROP FUNCTION IF EXISTS reject_audit_event_mutation()")
    op.execute("ALTER TABLE audit_events ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()")
    op.execute("ALTER TABLE audit_events DROP COLUMN IF EXISTS request_id")
    op.execute("ALTER TABLE audit_events DROP COLUMN IF EXISTS actor_id")
    op.execute("ALTER TABLE audit_events DROP COLUMN IF EXISTS actor_type")
    op.execute("ALTER TABLE audit_events DROP COLUMN IF EXISTS occurred_at")