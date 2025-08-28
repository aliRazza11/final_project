"""add image_frames table

Revision ID: 1607f997ba99
Revises: 6f7298c49fd1
Create Date: 2025-08-28 01:04:40.377126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1607f997ba99'
down_revision: Union[str, Sequence[str], None] = '6f7298c49fd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "image_frames",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("image_id", sa.Integer, sa.ForeignKey("images.id", ondelete="CASCADE"), nullable=False),
        sa.Column("local_t", sa.Integer, nullable=False),
        sa.Column("global_t", sa.Integer, nullable=False),
        sa.Column("frame_data", sa.LargeBinary(length=2**32 - 1), nullable=False),
        sa.Column("beta", sa.Float, nullable=True),
        sa.Column("metrics", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table("image_frames")