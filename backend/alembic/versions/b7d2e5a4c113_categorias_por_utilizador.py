"""categorias por utilizador

Revision ID: b7d2e5a4c113
Revises: a3f1c47b90de
Create Date: 2026-09-04 10:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7d2e5a4c113"
down_revision: Union[str, Sequence[str], None] = "a3f1c47b90de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    ligacao = op.get_bind()

    globais = ligacao.execute(
        sa.text("SELECT id, name, is_default FROM categories WHERE user_id IS NULL")
    ).all()
    if not globais:
        return

    utilizadores = ligacao.execute(sa.text("SELECT id FROM users")).all()

    for (user_id,) in utilizadores:
        for categoria_id, nome, is_default in globais:
            existe = ligacao.execute(
                sa.text("SELECT id FROM categories WHERE user_id = :user_id AND name = :nome"),
                {"user_id": user_id, "nome": nome},
            ).first()

            if existe is None:
                ligacao.execute(
                    sa.text(
                        "INSERT INTO categories (user_id, name, is_default)"
                        " VALUES (:user_id, :nome, :is_default)"
                    ),
                    {"user_id": user_id, "nome": nome, "is_default": is_default},
                )
                nova = ligacao.execute(
                    sa.text("SELECT id FROM categories WHERE user_id = :user_id AND name = :nome"),
                    {"user_id": user_id, "nome": nome},
                ).first()
                novo_id = nova[0]
            else:
                novo_id = existe[0]

            ligacao.execute(
                sa.text(
                    "UPDATE expenses SET category_id = :novo_id"
                    " WHERE user_id = :user_id AND category_id = :categoria_id"
                ),
                {"novo_id": novo_id, "user_id": user_id, "categoria_id": categoria_id},
            )

    ligacao.execute(
        sa.text(
            "UPDATE expenses SET category_id = NULL WHERE category_id IN"
            " (SELECT id FROM categories WHERE user_id IS NULL)"
        )
    )
    ligacao.execute(sa.text("DELETE FROM categories WHERE user_id IS NULL"))


def downgrade() -> None:
    """Downgrade schema."""
    ligacao = op.get_bind()

    nomes = ligacao.execute(
        sa.text("SELECT DISTINCT name FROM categories WHERE is_default = true")
    ).all()

    for (nome,) in nomes:
        ligacao.execute(
            sa.text(
                "INSERT INTO categories (user_id, name, is_default) VALUES (NULL, :nome, true)"
            ),
            {"nome": nome},
        )
        global_id = ligacao.execute(
            sa.text("SELECT id FROM categories WHERE user_id IS NULL AND name = :nome"),
            {"nome": nome},
        ).first()[0]

        ligacao.execute(
            sa.text(
                "UPDATE expenses SET category_id = :global_id WHERE category_id IN"
                " (SELECT id FROM categories WHERE user_id IS NOT NULL AND name = :nome)"
            ),
            {"global_id": global_id, "nome": nome},
        )

    ligacao.execute(
        sa.text(
            "UPDATE expenses SET category_id = NULL WHERE category_id IN"
            " (SELECT id FROM categories WHERE user_id IS NOT NULL)"
        )
    )
    ligacao.execute(sa.text("DELETE FROM categories WHERE user_id IS NOT NULL"))
