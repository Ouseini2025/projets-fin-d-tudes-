"""initial identity and multi-company schema

Revision ID: 20260920_01
Revises:
Create Date: 2026-09-20
"""
from alembic import op
import sqlalchemy as sa

revision = "20260920_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid_type = sa.Uuid()
    op.create_table("companies", sa.Column("id", uuid_type, nullable=False), sa.Column("name", sa.String(length=160), nullable=False), sa.Column("phone", sa.String(length=40), nullable=True), sa.Column("address", sa.String(length=255), nullable=True), sa.Column("currency", sa.String(length=8), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.PrimaryKeyConstraint("id"))
    op.create_table("roles", sa.Column("id", uuid_type, nullable=False), sa.Column("name", sa.String(length=40), nullable=False), sa.Column("description", sa.String(length=255), nullable=True), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("name"))
    op.create_index("ix_roles_name", "roles", ["name"])
    op.create_table("permissions", sa.Column("id", uuid_type, nullable=False), sa.Column("code", sa.String(length=100), nullable=False), sa.Column("description", sa.String(length=255), nullable=True), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("code"))
    op.create_index("ix_permissions_code", "permissions", ["code"])
    op.create_table("role_permissions", sa.Column("role_id", uuid_type, nullable=False), sa.Column("permission_id", uuid_type, nullable=False), sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("role_id", "permission_id"))
    op.create_table("users", sa.Column("id", uuid_type, nullable=False), sa.Column("company_id", uuid_type, nullable=False), sa.Column("role_id", uuid_type, nullable=False), sa.Column("full_name", sa.String(length=160), nullable=False), sa.Column("email", sa.String(length=255), nullable=False), sa.Column("hashed_password", sa.String(length=255), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("email"))
    op.create_index("ix_users_company_id", "users", ["company_id"])
    op.create_index("ix_users_email", "users", ["email"])


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_company_id", table_name="users")
    op.drop_table("users")
    op.drop_table("role_permissions")
    op.drop_index("ix_permissions_code", table_name="permissions")
    op.drop_table("permissions")
    op.drop_index("ix_roles_name", table_name="roles")
    op.drop_table("roles")
    op.drop_table("companies")
