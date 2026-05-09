"""dish ingredients

Revision ID: 002
Revises: 001
Create Date: 2026-04-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dish_ingredients",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("dish_id", UUID(as_uuid=True), sa.ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", UUID(as_uuid=True), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 3), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False),
    )
    op.create_index("ix_dish_ingredients_dish_id", "dish_ingredients", ["dish_id"])


def downgrade() -> None:
    op.drop_index("ix_dish_ingredients_dish_id", table_name="dish_ingredients")
    op.drop_table("dish_ingredients")
