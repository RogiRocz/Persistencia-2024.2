"""Cria esquema inicial

Revision ID: 37f0e315c791
Revises: 
Create Date: 2025-01-22 23:17:08.759079

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37f0e315c791'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'produtos',
        sa.Column('ID_Produto', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=50), nullable=False),
        sa.Column('valor_unitario', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.PrimaryKeyConstraint('ID_Produto')
    )

    op.create_table(
        'clientes',
        sa.Column('ID_Cliente', sa.Integer(), nullable=False),
        sa.Column('forma_pagamento', sa.String(length=20), nullable=False),
        sa.Column('programa_fidelidade', sa.String(length=15), nullable=True),
        sa.PrimaryKeyConstraint('ID_Cliente')
    )

    op.create_table(
        'vendas',
        sa.Column('ID_Venda', sa.Integer(), nullable=False),
        sa.Column('ID_Cliente', sa.Integer(), nullable=False),
        sa.Column('ID_Produto', sa.Integer(), nullable=False),
        sa.Column('quantidade', sa.Integer(), nullable=False),
        sa.Column('valor_total', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.PrimaryKeyConstraint('ID_Venda'),
        sa.ForeignKeyConstraint(['ID_Cliente'], ['clientes.ID_Cliente']),
        sa.ForeignKeyConstraint(['ID_Produto'], ['produtos.ID_Produto'])
    )

    op.create_table(
        'fornecedores',
        sa.Column('ID_Fornecedor', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=50), nullable=False),
        sa.Column('ID_Produto', sa.Integer(), nullable=False),
        sa.Column('quantidade', sa.Integer(), nullable=False),
        sa.Column('valor_unitario', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.PrimaryKeyConstraint('ID_Fornecedor'),
        sa.ForeignKeyConstraint(['ID_Produto'], ['produtos.ID_Produto'])
    )

    op.create_table(
        'estoque',
        sa.Column('ID_Estoque', sa.Integer(), nullable=False),
        sa.Column('ID_Fornecedor', sa.Integer(), nullable=False),
        sa.Column('ID_Produto', sa.Integer(), nullable=False),
        sa.Column('quantidade', sa.Integer(), nullable=False),
        sa.Column('categoria', sa.String(length=50), nullable=True),
        sa.Column('validade_dias', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('ID_Estoque'),
        sa.ForeignKeyConstraint(['ID_Fornecedor'], ['fornecedores.ID_Fornecedor']),
        sa.ForeignKeyConstraint(['ID_Produto'], ['produtos.ID_Produto'])
    )


def downgrade() -> None:
    op.drop_table('estoque')
    op.drop_table('fornecedores')
    op.drop_table('vendas')
    op.drop_table('clientes')
    op.drop_table('produtos')
