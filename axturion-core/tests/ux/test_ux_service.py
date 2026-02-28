import time

from app.domain.ux.models import (
    UXConfig,
)  # noqa: F401  (register model for Base.metadata)
from app.services.ux_service import get_ux_config, upsert_ux_config


def test_get_ux_config_returns_none_when_missing(db, ctx):
    assert get_ux_config(db, ctx, "applications") is None


def test_upsert_ux_config_creates_and_updates(db, ctx):
    created = upsert_ux_config(db, ctx, "applications", {"a": 1})

    assert created.organization_id == ctx.organization_id
    assert created.module == "applications"
    assert created.config == {"a": 1}

    fetched = get_ux_config(db, ctx, "applications")
    assert fetched is not None
    assert fetched.id == created.id

    old_updated_at = fetched.updated_at
    time.sleep(0.01)

    updated = upsert_ux_config(db, ctx, "applications", {"a": 2, "b": True})
    assert updated.id == created.id
    assert updated.config == {"a": 2, "b": True}
    assert updated.updated_at >= old_updated_at


def test_module_is_normalized_by_strip(db, ctx):
    upsert_ux_config(db, ctx, "  reporting  ", {"x": 1})

    fetched = get_ux_config(db, ctx, "reporting")
    assert fetched is not None
    assert fetched.module == "reporting"
    assert fetched.config == {"x": 1}
