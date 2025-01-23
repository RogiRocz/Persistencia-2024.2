from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from db_connect import get_db
from sqlalchemy.exc import SQLAlchemyError
from http import HTTPStatus
import os
import yaml
from alembic import command
from alembic.config import Config

from crud_produtos import route_produtos, Produtos
from crud_clientes import route_clientes, Clientes
from crud_vendas import route_vendas, Vendas
from crud_fornecedores import route_fornecedores, Fornecedores
from crud_estoque import route_estoque, Estoque

app = FastAPI()

curr_dir = os.path.abspath(os.path.dirname(__file__))
config_path = os.path.join(curr_dir, "config", "config.yaml")
with open(config_path, 'r') as config_file:
    tabelas = config_file['db_tables']

app.include_router(route_produtos('produtos'))
app.include_router(route_clientes('clientes'))
app.include_router(route_vendas('vendas'))
app.include_router(route_fornecedores('fornecedores'))
app.include_router(route_estoque('estoque'))

def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    
run_migrations()


@app.get('/quantidade_entidades')
def quantidade_entidades(db: Session=Depends(get_db)):
    resultado = dict()
    
    try:
        query_produtos = db.query(func.count(Produtos.ID_Produto))
        query_clientes = db.query(func.count(Clientes.ID_Cliente))
        query_vendas = db.query(func.count(Vendas.ID_Venda))
        query_fornecedores = db.query(func.count(Fornecedores.ID_Fornecedor))
        query_estoque = db.query(func.count(Estoque.ID_Estoque))
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao retornar os dados. Erro: {str(e)}")
    else:
        resultado.update({'Produtos': query_produtos, 'Clientes': query_clientes, 'Vendas': query_vendas, 'Fornecedores': query_fornecedores, 'Estoque': query_estoque})
        return resultado
    
@app.get('/atributos')
def get_atributos_especificos(entidade: str, db: Session=Depends(get_db), **attrs):
        
        entidade_modelo = {"produtos": Produtos, "clientes": Clientes, "vendas": Vendas, "fornecedores": Fornecedores, "estoque": Estoque}.get(entidade.lower())
        
        if not entidade_modelo:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='Entidade inválida')
        
        query = db.query(entidade_modelo)
        
        for key, value in attrs.items():
            if hasattr(entidade_modelo, key):
                query = query.filter(getattr(entidade_modelo, key) == value)
            else:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f"Atributo '{key}' não existe na entidade '{entidade}'.")
        
        resultado = query.all()
        return resultado