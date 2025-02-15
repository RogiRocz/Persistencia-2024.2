from fastapi import APIRouter, HTTPException, Request, Depends, Body
from db_connect import engine as db
from models import ProdutosFornecidos, Produtos, Fornecedores
from crud.pagination import PaginationParams
from typing import List, Optional
from bson import ObjectId
from http import HTTPStatus

def router_produtos_fornecidos():
    router = APIRouter(prefix='/produtos_fornecidos', tags=['produtos_fornecidos'])

    @router.get('/', response_model=List[ProdutosFornecidos], description="Lista todos os produtos fornecidos")
    async def listar_produtos_fornecidos():
        produtos_fornecidos = await db.find(ProdutosFornecidos)
        return produtos_fornecidos

    @router.get('/pagination', response_model=dict, description="Lista todos os produtos fornecidos com paginação")
    async def get_all_produtos_fornecidos_pagination(pag: PaginationParams = Depends()):
        result_produtos_fornecidos = await pag.pagination(db, ProdutosFornecidos)
        return {
            'resultado': result_produtos_fornecidos['resultado'],
            'prox_id': result_produtos_fornecidos['prox_id'],
            'tamanho': result_produtos_fornecidos['tamanho_pag'],
            'pagina_atual': result_produtos_fornecidos['pagina_atual'],
            'total_paginas': result_produtos_fornecidos['total_paginas']
        }
        
    @router.get('/atributos', response_model=List[ProdutosFornecidos], description="Busca produtos fornecidos por atributos específicos")
    async def get_produtos_fornecidos_especifico(
        id: Optional[str] = None,
        id_produto: Optional[str] = None,
        id_fornecedor: Optional[str] = None,
        quantidade: Optional[int] = None,
        custo_unidade: Optional[float] = None
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
        if id_fornecedor is not None:
            try:
                fornecedor = await db.find_one(Fornecedores, Fornecedores.id == ObjectId(id_fornecedor))
            except Exception:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Fornecedor não encontrado')
            filtros['fornecedor'] = fornecedor
        if quantidade is not None:
            filtros['quantidade'] = quantidade
        if custo_unidade is not None:
            filtros['custo_unidade'] = custo_unidade
        
        produtos_fornecidos = await db.find(ProdutosFornecidos, filtros)
        if not produtos_fornecidos:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Nenhum produto fornecido encontrado com os filtros fornecidos')
        
        return produtos_fornecidos
    
    @router.post('/', response_model=ProdutosFornecidos, description="Adiciona um novo produto fornecido")
    async def post_produto_fornecido(pf: ProdutosFornecidos = Body(
        ...,
        example={
            "produto": "60d5ec49f1e7e2a5d4e8b5b2",
            "fornecedor": "60d5ec49f1e7e2a5d4e8b5b4",
            "quantidade": 100,
            "custo_unidade": 15.0
        }
    )):
        produto = await db.find_one(Produtos, Produtos.id == ObjectId(pf.produto))
        if produto is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto não encontrado')
        
        fornecedor = await db.find_one(Fornecedores, Fornecedores.id == ObjectId(pf.fornecedor))
        if fornecedor is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Fornecedor não encontrado')
        
        novo_pf = ProdutosFornecidos(produto=produto, fornecedor=fornecedor, quantidade=pf.quantidade, custo_unidade=pf.custo_unidade)
        await db.save(novo_pf)
        return novo_pf

    @router.put('/{id_pf}', response_model=ProdutosFornecidos, description="Atualiza um produto fornecido existente")
    async def put_produto_fornecido(id_pf: str, pf_atualizado: ProdutosFornecidos):
        pf = await db.find_one(ProdutosFornecidos, ProdutosFornecidos.id == ObjectId(id_pf))
        if pf is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto fornecido não encontrado')
        
        produto = await db.find_one(Produtos, Produtos.id == ObjectId(pf_atualizado.produto.id))
        if produto is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto não encontrado')
        
        fornecedor = await db.find_one(Fornecedores, Fornecedores.id == ObjectId(pf_atualizado.fornecedor.id))
        if fornecedor is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Fornecedor não encontrado')
        
        pf.produto = produto
        pf.fornecedor = fornecedor
        pf.quantidade = pf_atualizado.quantidade if pf_atualizado.quantidade else pf.quantidade
        pf.custo_unidade = pf_atualizado.custo_unidade if pf_atualizado.custo_unidade else pf.custo_unidade
        
        await db.save(pf)
        return pf

    @router.delete('/{id_pf}', response_model=int, description="Deleta um produto fornecido existente")
    async def delete_produto_fornecido(id_pf: str):
        deleted_count = await db.delete(ProdutosFornecidos, ProdutosFornecidos.id == ObjectId(id_pf))
        if deleted_count == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto fornecido não encontrado')
        return deleted_count

    return router
