"""criar tabela login_tokens

Revision ID: a3f1c47b90de
Revises: cf446560cdcd
Create Date: 2026-09-03 12:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3f1c47b90de"
down_revision: Union[str, Sequence[str], None] = "cf446560cdcd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "login_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_login_tokens_code"), "login_tokens", ["code"], unique=False)
    op.create_index(op.f("ix_login_tokens_user_id"), "login_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_login_tokens_user_id"), table_name="login_tokens")
    op.drop_index(op.f("ix_login_tokens_code"), table_name="login_tokens")
    op.drop_table("login_tokens")
