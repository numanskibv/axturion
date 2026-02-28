import os
import random
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_request_context, require_scope
from app.core.db import get_db
from app.core.request_context import RequestContext
from app.core.scopes import APPLICATION_CREATE
from app.domain.application.models import Application
from app.domain.workflow.models import WorkflowStage
from app.services.audit_service import append_audit_log


router = APIRouter(prefix="/dev/seed", tags=["dev"])


class SeedLifecycleRequest(BaseModel):
    workflow_id: UUID
    open_count: int = Field(default=25, ge=0, le=500)
    closed_count: int = Field(default=10, ge=0, le=200)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@router.post(
    "/lifecycle",
    summary="Seed realistic lifecycle demo data (dev only)",
    description=(
        "DEV ONLY. Seeds applications with backdated timestamps so dashboard metrics look realistic "
        "(days/weeks rather than seconds). Also writes stage-change audit events with matching timestamps "
        "so lifecycle reporting endpoints return meaningful data."
    ),
)
def seed_lifecycle(
    body: SeedLifecycleRequest,
    _: None = Depends(require_scope(APPLICATION_CREATE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    if os.getenv("ENV", "dev").lower() == "prod":
        raise HTTPException(status_code=404, detail="Not found")

    stages = (
        db.query(WorkflowStage)
        .filter(
            WorkflowStage.workflow_id == body.workflow_id,
            WorkflowStage.organization_id == ctx.organization_id,
        )
        .order_by(WorkflowStage.order.asc().nullslast())
        .all()
    )
    stage_names = [s.name for s in stages if s.name]
    if not stage_names:
        raise HTTPException(status_code=400, detail="Workflow has no stages")

    # Assumption: first stage is the entry stage.
    entry_stage = stage_names[0]

    rng = random.Random(20260228)
    now = _now_utc()

    def pick_created_at() -> datetime:
        # Spread over ~60 days.
        days_ago = rng.randint(1, 60)
        hours = rng.randint(0, 23)
        return now - timedelta(days=days_ago, hours=hours)

    def append_stage_change(
        app_id: UUID, from_stage: str, to_stage: str, at: datetime
    ) -> None:
        append_audit_log(
            db,
            ctx,
            entity_type="application",
            entity_id=str(app_id),
            action="stage_changed",
            payload=f"{from_stage}->{to_stage}",
            created_at=at,
        )

    created_app_ids: list[str] = []

    def create_one(*, status: str, result: str | None) -> None:
        created_at = pick_created_at()

        # Choose a final stage.
        if status == "closed":
            final_stage = stage_names[-1]
        else:
            # Bias towards early stages.
            final_stage = rng.choices(
                population=stage_names,
                weights=[5, 3, 2, 1, 1][: len(stage_names)],
                k=1,
            )[0]

        # Build a progression from entry -> final.
        final_idx = stage_names.index(final_stage)
        progression = stage_names[: final_idx + 1]

        # Determine close time if needed.
        closed_at = None
        if status == "closed":
            ttc_days = rng.randint(10, 55)
            closed_at = created_at + timedelta(days=ttc_days, hours=rng.randint(0, 12))
            if closed_at > now - timedelta(hours=2):
                closed_at = now - timedelta(hours=2)

        # Create app row.
        app = Application(
            organization_id=ctx.organization_id,
            workflow_id=body.workflow_id,
            stage=final_stage,
            status=status,
            result=result,
            created_at=created_at,
            closed_at=closed_at,
            stage_entered_at=created_at,
        )
        db.add(app)
        db.flush()  # get app.id

        # Write stage-change audit events (backdated) and compute stage_entered_at.
        last_stage_time = created_at
        current = entry_stage

        # Distribute transitions across the timeline.
        if len(progression) > 1:
            end_at = closed_at or (now - timedelta(hours=2))
            if end_at <= created_at:
                end_at = created_at + timedelta(days=1)

            total_seconds = (end_at - created_at).total_seconds()
            steps = len(progression) - 1

            for i in range(steps):
                next_stage = progression[i + 1]

                # Place each transition roughly evenly across the window with jitter.
                base = created_at + timedelta(
                    seconds=total_seconds * (i + 1) / (steps + 1)
                )
                jitter = timedelta(hours=rng.randint(-12, 24))
                at = base + jitter

                # Keep monotonically increasing per-application.
                if at <= last_stage_time:
                    at = last_stage_time + timedelta(hours=1)
                if at >= end_at:
                    at = end_at - timedelta(hours=1)

                append_stage_change(app.id, current, next_stage, at)
                current = next_stage
                last_stage_time = at

        app.stage_entered_at = last_stage_time
        created_app_ids.append(str(app.id))

    # Create open apps
    for _i in range(int(body.open_count)):
        create_one(status="open", result=None)

    # Create closed apps
    for _i in range(int(body.closed_count)):
        result = rng.choice(["hired", "rejected"])
        create_one(status="closed", result=result)

    db.commit()

    return {
        "ok": True,
        "created": {
            "open": int(body.open_count),
            "closed": int(body.closed_count),
        },
        "application_ids": created_app_ids,
    }
