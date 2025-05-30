"""update: change to default message

Revision ID: fe7f16435759
Revises: b2667b3dfc7b
Create Date: 2025-05-19 20:46:39.452388

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fe7f16435759"
down_revision: str | None = "b2667b3dfc7b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("tasks", "message", existing_type=sa.VARCHAR(), nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("tasks", "message", existing_type=sa.VARCHAR(), nullable=True)
    # ### end Alembic commands ###
