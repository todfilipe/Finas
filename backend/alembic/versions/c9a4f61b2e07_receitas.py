"""receitas

Revision ID: c9a4f61b2e07
Revises: b7d2e5a4c113
Create Date: 2026-09-04 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9a4f61b2e07"
down_revision: Union[str, Sequence[str], None] = "b7d2e5a4c113"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CATEGORIAS_RECEITA = [
    "Salário",
    "Freelance",
    "Investimentos",
    "Reembolsos",
    "Presentes",
    "Outros",
]


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "categories",
        sa.Column("kind", sa.String(length=10), nullable=False, server_default="expense"),
    )
    op.add_column(
        "expenses",
        sa.Column("kind", sa.String(length=10), nullable=False, server_default="expense"),
    )
    op.create_index(op.f("ix_expenses_kind"), "expenses", ["kind"], unique=False)

    ligacao = op.get_bind()
    utilizadores = ligacao.execute(sa.text("SELECT id FROM users")).all()

    for (user_id,) in utilizadores:
        for nome in CATEGORIAS_RECEITA:
            existe = ligacao.execute(
                sa.text(
                    "SELECT id FROM categories"
                    " WHERE user_id = :user_id AND name = :nome AND kind = 'income'"
                ),
                {"user_id": user_id, "nome": nome},
            ).first()

            if existe is None:
                ligacao.execute(
                    sa.text(
                        "INSERT INTO categories (user_id, name, kind, is_default)"
                        " VALUES (:user_id, :nome, 'income', true)"
                    ),
                    {"user_id": user_id, "nome": nome},
                )


def downgrade() -> None:
    """Downgrade schema."""
    ligacao = op.get_bind()

    ligacao.execute(
        sa.text(
            "UPDATE expenses SET category_id = NULL WHERE category_id IN"
            " (SELECT id FROM categories WHERE kind = 'income')"
        )
    )
    ligacao.execute(sa.text("DELETE FROM expenses WHERE kind = 'income'"))
    ligacao.execute(sa.text("DELETE FROM categories WHERE kind = 'income'"))

    op.drop_index(op.f("ix_expenses_kind"), table_name="expenses")
    op.drop_column("expenses", "kind")
    op.drop_column("categories", "kind")
