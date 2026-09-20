from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import DbSession
from app.core.security import create_access_token
from app.schemas.auth import BootstrapAdminRequest, LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentification"])


def user_response(user) -> UserResponse:
    return UserResponse(id=str(user.id), company_id=str(user.company_id), full_name=user.full_name,
                        email=user.email, role=user.role.name, is_active=user.is_active)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def bootstrap_admin(payload: BootstrapAdminRequest, db: DbSession) -> TokenResponse:
    """Crée une entreprise et son premier administrateur."""
    try:
        user = AuthService().bootstrap_admin(db, **payload.model_dump())
        db.commit()
        db.refresh(user)
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    token = create_access_token(user.id, user.company_id, user.role.name)
    return TokenResponse(access_token=token, user=user_response(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = AuthService().authenticate(db, email=str(payload.email), password=payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Adresse e-mail ou mot de passe invalide.")
    return TokenResponse(access_token=create_access_token(user.id, user.company_id, user.role.name), user=user_response(user))
