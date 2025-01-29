from odmantic import Model, Field, Reference
from typing import Optional, List
from pydantic import field_validator
from decimal import Decimal

class Produtos(Model):
    codigo_barras: str = Field(unique=True, description='O código de barras é único para prdouto')
    nome: str
    valor_unitario: Decimal = Field(ge=0.00, description='O valor_unitario tem que ser positivo')
    
class Cliente(Model):
    forma_pagamento: str
    programa_fidelidade: Optional[str] = None
    
class ItemVenda(Model):
    produto: Produtos = Reference(key_name='id_produto')
    quantidade: int = Field(ge=0, description='A quantidade tem que ser positiva')
    
class Vendas(Model):
    cliente: Cliente = Reference(key_name='id_cliente')
    produtos: List[ItemVenda]
    valor_total: Decimal = Field(default=Decimal('0.00'))
    
    def calcular_valor_total(self):
        total = Decimal('0.00')
        for item in self.produtos:
            produto = item.produto
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
    cnpj: str = Field(regex=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$', description="Formato de CNPJ inválido")
    endereco: str
    
class ProdutosFornecidos(Model):
    produto: Produtos = Reference(key_name='id_produto')
    fornecedor : Fornecedores = Reference(key_name='id_fornecedor')
    quantidade: int = Field(ge=0)
    custo_unidade: Decimal = Field(ge=0.00)
    
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