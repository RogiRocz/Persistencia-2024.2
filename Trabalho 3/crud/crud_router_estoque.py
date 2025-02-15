from fastapi import APIRouter, Depends, HTTPException, Request
from db_connect import engine as db
from models import Produtos, Estoque
from crud.pagination import PaginationParams
from typing import List, Optional
from bson import ObjectId
from http import HTTPStatus

def router_estoque():
    router = APIRouter(prefix='/estoque', tags=['estoque'])
    
    @router.get('/', response_model=List[Estoque], description="Lista todos os itens de estoque")
    async def get_all_estoque():
        estoque = await db.find(Estoque)
        return estoque
    
    @router.get('/pagination', response_model=dict, description="Lista todos os itens de estoque com paginação")
    async def get_all_estoque_pagination(pag: PaginationParams = Depends()):
        result_estoque = await pag.pagination(db, Estoque)
        return {
            'resultado': result_estoque['resultado'],
            'prox_id': result_estoque['prox_id'],
            'tamanho': result_estoque['tamanho_pag'],
            'pagina_atual': result_estoque['pagina_atual'],
            'total_paginas': result_estoque['total_paginas']
        }
    
    @router.get('/atributos', response_model=List[Estoque], description="Obtém itens de estoque específicos pelos atributos fornecidos")
    async def get_estoque_especifico(
        id: Optional[str] = None,
        id_produto: Optional[str] = None,
        quantidade: Optional[int] = None,
        validade_dias: Optional[int] = None
    ):
        filtros = {}
        
        if id is not None:
            filtros['_id'] = ObjectId(id)
        if id_produto is not None:
            try:
                produto = await db.find_one(Produtos, Produtos.id == ObjectId(id_produto))
            except Exception:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto não encontrado')
            filtros['produto'] = produto
        if quantidade is not None:
            filtros['quantidade'] = quantidade
        if validade_dias is not None:
            filtros['validade_dias'] = validade_dias
        
        estoque = await db.find(Estoque, filtros)
        if not estoque:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Nenhum item de estoque encontrado com os filtros fornecidos')
        
        return estoque
        
    @router.post('/', response_model=Estoque, description="Adiciona um novo item de estoque")
    async def post_estoque(estoque: Estoque):
        produto = await db.find_one(Produtos, Produtos.id == ObjectId(estoque.produto.id))
        if produto is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto não encontrado')
        
        novo_estoque = Estoque(
            produto=produto,
            quantidade=estoque.quantidade,
            validade_dias=estoque.validade_dias
        )
        
        await db.save(novo_estoque)
        return novo_estoque

    @router.put('/{id_estoque}', response_model=Estoque, description="Atualiza um item de estoque existente")
    async def put_estoque(id_estoque: str, estoque_atualizado: Estoque):
        estoque = await db.find_one(Estoque, Estoque.id == ObjectId(id_estoque))
        if estoque is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Item de estoque não encontrado')
        
        produto = await db.find_one(Produtos, Produtos.id == ObjectId(estoque_atualizado.produto.id))
        if produto is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto não encontrado')
        
        estoque.produto = produto
        estoque.quantidade = estoque_atualizado.quantidade if estoque_atualizado.quantidade else estoque.quantidade
        estoque.validade_dias = estoque_atualizado.validade_dias if estoque_atualizado.validade_dias else estoque.validade_dias
        
        await db.save(estoque)
        return estoque

    @router.delete('/{id_estoque}', response_model=int, description="Deleta um item de estoque existente")
    async def delete_estoque(id_estoque: str):
        deleted_count = await db.delete(Estoque, Estoque.id == ObjectId(id_estoque))
        if deleted_count == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Item de estoque não encontrado')
        return deleted_count

    return router
