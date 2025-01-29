from odmantic import Model, Field, Reference
from typing import Optional, List
from pydantic import field_validator
from decimal import Decimal
import re

class Produtos(Model):
    codigo_barras: str = Field(unique=True, description='O código de barras é único para produto')
    nome: str
    valor_unitario: Decimal = Field(ge=0.00, description='O valor_unitario tem que ser positivo')
    
class Clientes(Model):
    forma_pagamento: str
    programa_fidelidade: Optional[str] = None
    
class ItemVenda(Model):
    produto: Produtos = Reference(key_name='id_produto')
    quantidade: int = Field(ge=1, description='A quantidade tem que ser positiva')
    
class Vendas(Model):
    cliente: Clientes = Reference(key_name='id_cliente')
    produtos: List[ItemVenda]
    valor_total: Decimal = Field(default=Decimal('0.00'))
    
    def calcular_valor_total(self):
        total = Decimal('0.00')
        for item in self.produtos:
            produto = item.produto
            if not produto.valor_unitario:
                raise ValueError(f'O valor_unitario de {produto.codigo_barras} não pode ser nulo')
            else:
                total += produto.valor_unitario * item.quantidade
            
        return total
    
    @field_validator('valor_total', mode='after')
    @classmethod
    def valida_valor_total(cls, valor):
        if valor > 10**8:
            raise ValueError('O valor_total tem mais de 10 dígitos')
        
        if round(valor, 2) != valor:
            raise ValueError('O valor_total tem mais de duas casas decimais')
    
    def __post_init__(self):
        self.valor_total = self.calcula_valor_total()
    
class Fornecedores(Model):
    nome: str
    cnpj: str = Field(unique=True)
    endereco: str
    
    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, valor: str) -> str:
        padrao_cnpj = r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$"
        if not re.match(padrao_cnpj, valor):
            raise ValueError("CNPJ inválido! Use o formato 00.000.000/0000-00")
        return valor
    
class ProdutosFornecidos(Model):
    produto: Produtos = Reference(key_name='id_produto')
    fornecedor : Fornecedores = Reference(key_name='id_fornecedor')
    quantidade: int = Field(ge=0)
    custo_unidade: Decimal = Field(ge=0.00, default=Decimal('0.00'))
    
    @field_validator('custo_unidade', mode='after')
    @classmethod
    def valida_custo_unidade(cls, valor):
        if valor > 10**8:
            raise ValueError('O custo_unidade tem mais de 10 dígitos')
        
        if round(valor, 2) != valor:
            raise ValueError('O custo_unidade tem mais de duas casas decimais')
    
    
    
class Estoque(Model):
    produto: Produtos = Reference(key_name='id_produto')
    quantidade: int = Field(ge=0, description='A quantidade deve ser maior que 0')
    validade_dias: int = Field(ge=0, description='A validade tem que ser positiva')