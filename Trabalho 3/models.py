from odmantic import Model, Field, Reference
from typing import Optional, List
from pydantic import field_validator
import re

class Produtos(Model):
    codigo_barras: str = Field(unique=True, description='O código de barras é único para produto')
    nome: str
    valor_unitario: float
    
class Clientes(Model):
    forma_pagamento: str
    programa_fidelidade: Optional[str] = None
    
class ItemVenda(Model):
    produto: Produtos = Reference(key_name='id_produto')
    quantidade: int = Field(ge=1, description='A quantidade tem que ser maior que 0')
    
class Vendas(Model):
    cliente: Clientes = Reference(key_name='id_cliente')
    produtos: List[ItemVenda]
    valor_total: float
    
    def calcular_valor_total(self):
        total = 0
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
        
        return valor

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
    quantidade: int = Field(ge=1)
    custo_unidade: float
    
    @field_validator('custo_unidade', mode='after')
    @classmethod
    def valida_custo_unidade(cls, valor):                    
        if valor > 10**8:
            raise ValueError('O custo_unidade tem mais de 10 dígitos')
        
        if round(valor, 2) != valor:
            raise ValueError('O custo_unidade tem mais de duas casas decimais')
        
        return valor
    
class Estoque(Model):
    produto: Produtos = Reference(key_name='id_produto')
    quantidade: int = Field(ge=1, description='A quantidade deve ser maior que 0')
    validade_dias: int = Field(ge=0, description='A validade tem que ser positiva')