from sqlalchemy import Column, Integer, Float, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Produtos(Base):
    __tablename__ = "produtos"
    ID_Produto = Column(Integer, primary_key=True)
    nome = Column(String(50), nullable=False)
    valor_unitario = Column(Numeric(10, 2), nullable=False)

    vendas = relationship("Vendas", back_populates="produtos")
    fornecedores = relationship("Fornecedores", back_populates="produtos")
    estoque = relationship("Estoque", back_populates="produtos", uselist=False)

class Clientes(Base):
    __tablename__ = "clientes"
    ID_Cliente = Column(Integer, primary_key=True)
    forma_pagamento = Column(String(20), nullable=False)
    programa_fidelidade = Column(String(15), nullable=True)

    vendas = relationship("Vendas", back_populates="clientes")


class Vendas(Base):
    __tablename__ = "vendas"
    ID_Venda = Column(Integer, primary_key=True)
    ID_Cliente = Column(Integer, ForeignKey("clientes.ID_Cliente"), nullable=False)
    ID_Produto = Column(Integer, ForeignKey("produtos.ID_Produto"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    valor_total = Column(Numeric(10, 2), nullable=False)  # Numeric para valores financeiros

    produtos = relationship("Produtos", back_populates="vendas")
    clientes = relationship("Clientes", back_populates="vendas")


class Fornecedores(Base):
    __tablename__ = "fornecedores"
    ID_Fornecedor = Column(Integer, primary_key=True)
    cnpj = Column(String(14), nullable=False)
    nome = Column(String(50), nullable=False)
    ID_Produto = Column(Integer, ForeignKey("produtos.ID_Produto"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    valor_unitario = Column(Numeric(10, 2), nullable=False)

    produtos = relationship("Produtos", back_populates="fornecedores")
    estoque = relationship("Estoque", back_populates="fornecedores")


class Estoque(Base):
    __tablename__ = "estoque"
    ID_Estoque = Column(Integer, primary_key=True)
    ID_Fornecedor = Column(Integer, ForeignKey("fornecedores.ID_Fornecedor"), nullable=False)
    ID_Produto = Column(Integer, ForeignKey("produtos.ID_Produto"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    categoria = Column(String(50), nullable=True)
    validade_dias = Column(Integer, nullable=False)

    produtos = relationship("Produtos", back_populates="estoque")
    fornecedores = relationship("Fornecedores", back_populates="estoque", uselist=True)
