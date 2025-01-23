"""Adicionando o atributo cnpj a tabela Fornecedores

Revision ID: 752b11ae096e
Revises: 37f0e315c791
Create Date: 2025-01-22 23:40:27.460849

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '752b11ae096e'
down_revision: Union[str, None] = '37f0e315c791'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('fornecedores', sa.Column('cnpj', sa.String(length=14), nullable=True))



def downgrade() -> None:
    op.drop_column('fornecedores', 'cnpj')