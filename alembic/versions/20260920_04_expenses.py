"""create expenses table

Revision ID: 20260920_04
Revises: 20260920_03
Create Date: 2026-09-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260920_04"
down_revision: Union[str, None] = "20260920_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expenses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.String(length=40),
            nullable=False,
        ),
        sa.Column(
            "amount",
            sa.Numeric(precision=14, scale=2),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "expense_date",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_expenses_company_id",
        "expenses",
        ["company_id"],
        unique=False,
    )

    op.create_index(
        "ix_expenses_user_id",
        "expenses",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_expenses_category",
        "expenses",
        ["category"],
        unique=False,
    )

    op.create_index(
        "ix_expenses_expense_date",
        "expenses",
        ["expense_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_expenses_expense_date", table_name="expenses")
    op.drop_index("ix_expenses_category", table_name="expenses")
    op.drop_index("ix_expenses_user_id", table_name="expenses")
    op.drop_index("ix_expenses_company_id", table_name="expenses")
    op.drop_table("expenses")