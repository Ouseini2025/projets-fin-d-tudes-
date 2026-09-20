"""catalog and stock

Revision ID: 20260920_02
Revises: 20260920_01
"""
from alembic import op
import sqlalchemy as sa

revision="20260920_02"
down_revision="20260920_01"
branch_labels=None
depends_on=None

def upgrade() -> None:
    u=sa.Uuid()
    op.create_table("categories",sa.Column("id",u,nullable=False),sa.Column("company_id",u,nullable=False),sa.Column("name",sa.String(120),nullable=False),sa.Column("description",sa.Text()),sa.Column("is_active",sa.Boolean(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("CURRENT_TIMESTAMP"),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("CURRENT_TIMESTAMP"),nullable=False),sa.ForeignKeyConstraint(["company_id"],["companies.id"],ondelete="RESTRICT"),sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_categories_company_id","categories",["company_id"])
    op.create_index("uq_active_category_name_per_company","categories",["company_id","name"],unique=True,postgresql_where=sa.text("is_active"))
    op.create_table("products",sa.Column("id",u,nullable=False),sa.Column("company_id",u,nullable=False),sa.Column("category_id",u),sa.Column("name",sa.String(160),nullable=False),sa.Column("sku",sa.String(80)),sa.Column("barcode",sa.String(80)),sa.Column("description",sa.Text()),sa.Column("purchase_price",sa.Numeric(14,2),nullable=False),sa.Column("selling_price",sa.Numeric(14,2),nullable=False),sa.Column("current_stock",sa.Integer(),nullable=False),sa.Column("minimum_stock",sa.Integer(),nullable=False),sa.Column("unit",sa.String(30),nullable=False),sa.Column("is_active",sa.Boolean(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("CURRENT_TIMESTAMP"),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),server_default=sa.text("CURRENT_TIMESTAMP"),nullable=False),sa.CheckConstraint("purchase_price >= 0",name="ck_products_purchase_price_non_negative"),sa.CheckConstraint("selling_price >= 0",name="ck_products_selling_price_non_negative"),sa.CheckConstraint("current_stock >= 0",name="ck_products_current_stock_non_negative"),sa.CheckConstraint("minimum_stock >= 0",name="ck_products_minimum_stock_non_negative"),sa.ForeignKeyConstraint(["company_id"],["companies.id"],ondelete="RESTRICT"),sa.ForeignKeyConstraint(["category_id"],["categories.id"],ondelete="SET NULL"),sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_products_company_id","products",["company_id"]);op.create_index("ix_products_category_id","products",["category_id"]);op.create_index("ix_products_sku","products",["sku"]);op.create_index("ix_products_barcode","products",["barcode"]);op.create_index("ix_products_company_name","products",["company_id","name"])
    op.create_table("stock_movements",sa.Column("id",u,nullable=False),sa.Column("company_id",u,nullable=False),sa.Column("product_id",u,nullable=False),sa.Column("user_id",u,nullable=False),sa.Column("movement_type",sa.String(20),nullable=False),sa.Column("quantity",sa.Integer(),nullable=False),sa.Column("stock_before",sa.Integer(),nullable=False),sa.Column("stock_after",sa.Integer(),nullable=False),sa.Column("reason",sa.Text()),sa.Column("reference",sa.String(100)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("CURRENT_TIMESTAMP"),nullable=False),sa.CheckConstraint("quantity > 0",name="ck_stock_movements_quantity_positive"),sa.ForeignKeyConstraint(["company_id"],["companies.id"],ondelete="RESTRICT"),sa.ForeignKeyConstraint(["product_id"],["products.id"],ondelete="RESTRICT"),sa.ForeignKeyConstraint(["user_id"],["users.id"],ondelete="RESTRICT"),sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_stock_movements_company_id","stock_movements",["company_id"]);op.create_index("ix_stock_movements_product_id","stock_movements",["product_id"]);op.create_index("ix_stock_movements_user_id","stock_movements",["user_id"]);op.create_index("ix_stock_movements_movement_type","stock_movements",["movement_type"])

def downgrade() -> None:
    op.drop_table("stock_movements");op.drop_table("products");op.drop_table("categories")
