from typing import Any

from sqlalchemy.orm import Session

from app.domain.ux.models import UXConfig
from app.core.request_context import RequestContext


def get_ux_config(db: Session, ctx: RequestContext, module: str) -> UXConfig | None:
    module = (module or "").strip()
    if not module:
        raise ValueError("module is required")

    return (
        db.query(UXConfig)
        .filter(
            UXConfig.organization_id == ctx.organization_id,
            UXConfig.module == module,
        )
        .order_by(UXConfig.updated_at.desc())
        .first()
    )


def upsert_ux_config(
    db: Session,
    ctx: RequestContext,
    module: str,
    config_data: dict[str, Any],
    *,
    commit: bool = True,
) -> UXConfig:
    module = (module or "").strip()
    if not module:
        raise ValueError("module is required")
    if not isinstance(config_data, dict):
        raise TypeError("config_data must be a dict")

    existing = (
        db.query(UXConfig)
        .filter(
            UXConfig.organization_id == ctx.organization_id,
            UXConfig.module == module,
        )
        .order_by(UXConfig.updated_at.desc())
        .first()
    )

    if existing:
        existing.config = config_data
        if commit:
            db.commit()
        else:
            db.flush()
        db.refresh(existing)
        return existing

    new_config = UXConfig(
        organization_id=ctx.organization_id,
        module=module,
        config=config_data,
    )
    db.add(new_config)
    if commit:
        db.commit()
    else:
        db.flush()
    db.refresh(new_config)
    return new_config
