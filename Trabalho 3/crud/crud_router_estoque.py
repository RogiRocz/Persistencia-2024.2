from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from db_connect import engine as db
from models import Estoque, Produtos
from pagination import PaginationParams
from typing import List, Optional
from bson import ObjectId
from http import HTTPStatus

class EstoquePy(BaseModel):
    id: Optional[str] = None
    produto: str # id do produto
    quantidade: int
    validade_dias: int

def router_estoque():
    router = APIRouter(prefix='/estoque', tags=['estoque'])
    
    @router.get('/', response_model=List[EstoquePy])
    async def get_all_estoque():
        estoque = await db.find(Estoque)
        
        response = [
            EstoquePy(
                id=str(e.id),
                produto=str(e.produto.id),
                quantidade=e.quantidade,
                validade_dias=e.validade_dias
            ) for e in estoque
        ]
        
        return response
    
    router.get('/pagination', response_model=List[EstoquePy])
    async def get_all_estoque_pagination(pag: PaginationParams):
        ultimo_id = pag.ultimo_id
        if ultimo_id is None:
            ultimo_id = await db.find_one(Estoque, sort=Estoque.id)
        
        result_estoque = await db.find(Estoque, Estoque.id > ObjectId(ultimo_id), limit=pag.tamanho)

        return [
            EstoquePy(
                id=str(estoque.id),
                produto=estoque.produto,
                quantidade=estoque.quantidade,
                validade_dias=estoque.validade_dias
            ) for estoque in result_estoque
        ]
    
    @router.get('/atributos', response_model=List[EstoquePy])
    async def get_estoque_especifico(req: Request):
        atributos = req.query_params
            
        filtros = {}
        
        for chave, valor in atributos.items():
            if chave in Estoque.model_fields:
                tipo_chave = Estoque.model_fields[chave].annotation
                try:
                    valor_convertido = tipo_chave(valor)
                except (ValueError, TypeError):
                    raise HTTPException(
                        status_code=HTTPStatus.BAD_REQUEST, detail=f"Valor inválido para o atributo {chave}. Esperado: {tipo_chave}"
                    )
                
                filtros[chave] = valor_convertido
        
        estoque = await db.find(Estoque, filtros)
        
        if not estoque:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Nenhum item de estoque encontrado com os filtros fornecidos')
        
        return [
            EstoquePy(
                id=str(e.id),
                produto=str(e.produto.id),
                quantidade=e.quantidade,
                validade_dias=e.validade_dias
            ) for e in estoque
        ]
        
    @router.post('/', response_model=EstoquePy)
    async def post_estoque(estoque: EstoquePy):
        produto = await db.find_one(Produtos, Produtos.id == ObjectId(estoque.produto))
        if produto is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto não encontrado')
        
        novo_estoque = Estoque(
            produto=produto,
            quantidade=estoque.quantidade,
            validade_dias=estoque.validade_dias
        )
        
        await db.save(novo_estoque)
        
        return EstoquePy(
            id=str(novo_estoque.id),
            produto=str(novo_estoque.produto.id),
            quantidade=novo_estoque.quantidade,
            validade_dias=novo_estoque.validade_dias
        )

    @router.put('/{id_estoque}', response_model=EstoquePy)
    async def put_estoque(id_estoque: str, estoque_atualizado: EstoquePy):
        estoque = await db.find_one(Estoque, Estoque.id == ObjectId(id_estoque))
        if estoque is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Item de estoque não encontrado')
        
        produto = await db.find_one(Produtos, Produtos.id == ObjectId(estoque_atualizado.produto))
        if produto is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto não encontrado')
        
        estoque.produto = produto
        estoque.quantidade = estoque_atualizado.quantidade
        estoque.validade_dias = estoque_atualizado.validade_dias
        
        await db.save(estoque)
        
        return EstoquePy(
            id=str(estoque.id),
            produto=str(estoque.produto.id),
            quantidade=estoque.quantidade,
            validade_dias=estoque.validade_dias
        )

    @router.delete('/{id_estoque}', response_model=int)
    async def delete_estoque(id_estoque: str):
        deleted_count = await db.delete(Estoque, Estoque.id == ObjectId(id_estoque))
        
        if deleted_count == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Item de estoque não encontrado')
        
        return deleted_count

    return router
