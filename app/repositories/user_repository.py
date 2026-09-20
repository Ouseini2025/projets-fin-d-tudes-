from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.user import User


class UserRepository:
    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).options(joinedload(User.role)).where(User.email == email.lower()))

    def get_by_id(self, db: Session, user_id: UUID) -> User | None:
        return db.scalar(select(User).options(joinedload(User.role)).where(User.id == user_id))

    def add(self, db: Session, user: User) -> User:
        db.add(user)
        db.flush()
        return user
