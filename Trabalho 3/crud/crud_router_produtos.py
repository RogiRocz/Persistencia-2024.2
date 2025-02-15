from fastapi import APIRouter, HTTPException, Request, Depends
from db_connect import engine as db
from models import Produtos
from crud.pagination import PaginationParams
from typing import List, Optional
from bson import ObjectId
from http import HTTPStatus

def router_produtos():
    router = APIRouter(prefix='/produtos', tags=['produtos'])

    @router.get('/', response_model=List[Produtos], description="Lista todos os produtos")
    async def get_all_produtos():
        produtos = await db.find(Produtos)
        return produtos
    
    @router.get('/pagination', response_model=dict, description="Lista todos os produtos com paginação")
    async def get_all_produtos_pagination(pag: PaginationParams = Depends()):
        result_produtos = await pag.pagination(db, Produtos)
        return {
            'resultado': result_produtos['resultado'],
            'prox_id': result_produtos['prox_id'],
            'tamanho': result_produtos['tamanho_pag'],
            'pagina_atual': result_produtos['pagina_atual'],
            'total_paginas': result_produtos['total_paginas']
        }
        
    @router.get('/atributos', response_model=List[Produtos], description="Lista produtos com base em atributos específicos")
    async def get_produtos_especifico(
        id: Optional[str] = None,
        nome: Optional[str] = None,
        codigo_barras: Optional[str] = None,
        valor_unitario: Optional[float] = None
    ):
        filtros = {}
        
        if id is not None:
            filtros['_id'] = ObjectId(id)
        if nome is not None:
            filtros['nome'] = {"$regex": f".*{nome}.*", "$options": "i"}
        if codigo_barras is not None:
            filtros['codigo_barras'] = codigo_barras
        if valor_unitario is not None:
            filtros['valor_unitario'] = valor_unitario
                
        produtos = await db.find(Produtos, filtros)
        if not produtos:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Nenhum produto encontrado com os filtros fornecidos')
                    
        return produtos

    @router.post('/', response_model=Produtos, description="Adiciona um novo produto")
    async def post_produto(produto: Produtos):
        await db.save(produto)
        return produto
        
    @router.put('/{id_produto}', response_model=Produtos, description="Atualiza um produto existente")
    async def put_produto(id_produto: str, novo_produto: Produtos):
        antigo_produto = await db.find_one(Produtos, Produtos.id == ObjectId(id_produto))
        if antigo_produto is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Produto não encontrado')
        
        antigo_produto.nome = novo_produto.nome if novo_produto.nome else antigo_produto.nome
        antigo_produto.codigo_barras = novo_produto.codigo_barras if novo_produto.codigo_barras else antigo_produto.codigo_barras
        antigo_produto.valor_unitario = novo_produto.valor_unitario if novo_produto.valor_unitario else antigo_produto.valor_unitario
                
        await db.save(antigo_produto)
        return antigo_produto
    
    @router.delete('/{id_produto}', response_model=int, description="Deleta um produto existente")
    async def delete_produto(id_produto: str):
        deleted_count = await db.remove(Produtos, Produtos.id == ObjectId(id_produto), just_one=True)
        if deleted_count == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Produto não encontrado')
        return deleted_count
        
    return router