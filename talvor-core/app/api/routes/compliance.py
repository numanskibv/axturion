from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_request_context, require_scope
from app.core.db import get_db
from app.core.request_context import RequestContext
from app.core.scopes import COMPLIANCE_EXPORT
from app.services.compliance_service import generate_compliance_bundle


router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get(
    "/export",
    summary="Download organization compliance export bundle",
    description="Exports an organization-scoped compliance bundle as a ZIP file.",
)
def export_bundle(
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _: None = Depends(require_scope(COMPLIANCE_EXPORT)),
):
    bundle = generate_compliance_bundle(db, ctx)

    filename = f"compliance_export_{ctx.organization_id}.zip"
    return Response(
        content=bundle,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
