from backend.app.db.session import Base
from backend.app.models import domain  # noqa: F401


def test_initial_schema_contains_required_entities():
    required = {"organizations", "users", "data_sources", "datasets", "ingestion_runs", "addresses", "assets", "transactions", "listings", "market_metrics", "signals", "audit_events"}
    assert required.issubset(Base.metadata.tables)


def test_ingestible_entities_have_source_record_id_uniqueness():
    for table_name in ("assets", "transactions", "listings", "market_metrics", "signals"):
        table = Base.metadata.tables[table_name]
        assert any("source_record_id" in constraint.columns.keys() for constraint in table.constraints if constraint.name and constraint.name.startswith("uq_"))