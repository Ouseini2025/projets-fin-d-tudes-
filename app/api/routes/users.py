from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import DbSession, require_roles

from app.api.deps import get_current_user
from app.api.routes.auth import user_response
from app.models.user import User
from app.schemas.auth import CreateUserRequest, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/users", tags=["utilisateurs"])


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserResponse:
    return user_response(current_user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: CreateUserRequest, db: DbSession,
                current_user: User = Depends(require_roles("ADMIN"))) -> UserResponse:
    """Crée un utilisateur dans l'entreprise de l'administrateur connecté."""
    try:
        user = AuthService().create_user(db, company_id=current_user.company_id,
                                         full_name=payload.full_name, email=str(payload.email),
                                         password=payload.password, role_name=payload.role)
        db.commit()
        db.refresh(user)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return user_response(user)
