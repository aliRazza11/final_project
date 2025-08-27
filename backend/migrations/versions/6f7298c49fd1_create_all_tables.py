"""create all tables

Revision ID: 6f7298c49fd1
Revises: 
Create Date: 2025-08-26 16:07:52.033696

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '6f7298c49fd1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    # non-unique index on username
    op.create_index("ix_users_username", "users", ["username"], unique=False)
    # unique index on email
    op.create_index("uq_users_email", "users", ["email"], unique=True)

    # --- images ---
    op.create_table(
        "images",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        # MEDIUMBLOB for up to ~16MB (your model uses LargeBinary(2**24 - 1))
        sa.Column("image_data", mysql.MEDIUMBLOB(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
    )
    op.create_table(
        'mnist',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('digit', sa.Integer, nullable=False, index=True),  # 0–9
        sa.Column('sample_index', sa.Integer, nullable=False),       # 1–20
        sa.Column('image_data', sa.LargeBinary, nullable=False),     # actual image bytes
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('digit', 'sample_index', name='uq_mnist_digit_sample')
    )


def downgrade() -> None:
    op.drop_table("images")
    op.drop_index("uq_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
 