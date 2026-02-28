from __future__ import annotations

from datetime import datetime, timedelta, timezone


def test_list_stage_aging_window_filters_audit_events_only(db, org, ctx, monkeypatch):
    from app.domain.application.models import Application
    from app.domain.workflow.models import Workflow
    from app.reporting.window import ReportingWindow
    from app.services.audit_service import append_audit_log
    from app.services.lifecycle_reporting_service import list_stage_aging

    wf = Workflow(organization_id=org.id, name="wf")
    db.add(wf)
    db.commit()
    db.refresh(wf)

    now = datetime(2026, 2, 28, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(
        "app.services.lifecycle_reporting_service._now_utc", lambda: now
    )

    # App A: has audits both inside and outside the window; must pick latest INSIDE window.
    a_created = now - timedelta(seconds=1000)
    app_a = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="screening",
        status="active",
        created_at=a_created,
        stage_entered_at=a_created,
    )

    # App B: has only an audit OUTSIDE the window; must fall back to created_at.
    b_created = now - timedelta(seconds=2000)
    app_b = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="applied",
        status="active",
        created_at=b_created,
        stage_entered_at=b_created,
    )

    db.add_all([app_a, app_b])
    db.commit()
    db.refresh(app_a)
    db.refresh(app_b)

    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app_a.id),
        action="stage_changed",
        payload="x->y",
        created_at=now - timedelta(seconds=500),  # outside window
    )
    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app_a.id),
        action="stage_transition_approved",
        payload={"from_stage": "y", "to_stage": "z"},
        created_at=now - timedelta(seconds=50),  # inside window
    )
    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app_a.id),
        action="stage_changed",
        payload="z->w",
        created_at=now - timedelta(seconds=10),  # outside window (after to_datetime)
    )

    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app_b.id),
        action="stage_changed",
        payload="a->b",
        created_at=now - timedelta(seconds=500),  # outside window
    )

    db.commit()

    window = ReportingWindow(
        from_datetime=now - timedelta(seconds=200),
        to_datetime=now - timedelta(seconds=20),
    )

    items = list_stage_aging(
        db, ctx, workflow_id=wf.id, window=window, limit=50, offset=0
    )
    by_id = {str(row["application_id"]): row for row in items}

    assert str(app_a.id) in by_id
    assert str(app_b.id) in by_id

    assert by_id[str(app_a.id)]["age_seconds"] == 50
    assert by_id[str(app_b.id)]["age_seconds"] == 2000
