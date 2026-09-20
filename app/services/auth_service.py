from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.company import Company
from app.models.rbac import Role
from app.models.user import User
from app.repositories.user_repository import UserRepository

ROLE_DESCRIPTIONS = {
    "ADMIN": "Gestion complète de l'entreprise.",
    "GERANT": "Gestion et consultation de l'activité.",
    "GESTIONNAIRE": "Opérations métier selon permissions.",
    "EMPLOYE": "Opérations explicitement autorisées.",
}


def ensure_default_roles(db: Session) -> None:
    existing = set(db.scalars(select(Role.name)).all())
    for name, description in ROLE_DESCRIPTIONS.items():
        if name not in existing:
            db.add(Role(name=name, description=description))
    db.flush()


class AuthService:
    def __init__(self, users: UserRepository | None = None) -> None:
        self.users = users or UserRepository()

    def bootstrap_admin(self, db: Session, *, company_name: str, full_name: str, email: str, password: str) -> User:
        if self.users.get_by_email(db, email):
            raise ValueError("Un compte existe déjà avec cette adresse e-mail.")
        ensure_default_roles(db)
        admin_role = db.scalar(select(Role).where(Role.name == "ADMIN"))
        if admin_role is None:
            raise RuntimeError("Le rôle ADMIN est introuvable.")
        company = Company(name=company_name)
        db.add(company)
        db.flush()
        return self.users.add(db, User(
            company_id=company.id,
            role_id=admin_role.id,
            full_name=full_name,
            email=email.lower(),
            hashed_password=hash_password(password),
        ))

    def authenticate(self, db: Session, *, email: str, password: str) -> User | None:
        user = self.users.get_by_email(db, email)
        if user is None or not user.is_active or not verify_password(password, user.hashed_password):
            return None
        return user

    def create_user(self, db: Session, *, company_id, full_name: str, email: str, password: str, role_name: str) -> User:
        if self.users.get_by_email(db, email):
            raise ValueError("Un compte existe déjà avec cette adresse e-mail.")
        role = db.scalar(select(Role).where(Role.name == role_name))
        if role is None:
            raise ValueError("Rôle invalide.")
        return self.users.add(db, User(company_id=company_id, role_id=role.id, full_name=full_name,
                                       email=email.lower(), hashed_password=hash_password(password)))
