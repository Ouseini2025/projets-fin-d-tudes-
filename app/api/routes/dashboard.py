from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import DbSession, require_roles
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import DashboardError, DashboardService


router = APIRouter(tags=["dashboard"])

service = DashboardService()


@router.get(
    "",
    response_model=DashboardSummary,
)
def get_dashboard(
    db: DbSession,
    user=Depends(
        require_roles(
            "ADMIN",
            "GERANT",
            "GESTIONNAIRE",
            "EMPLOYE",
        )
    ),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
):
    try:
        return service.get_summary(
            db,
            user,
            date_from=date_from,
            date_to=date_to,
        )
    except DashboardError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    