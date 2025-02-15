from fastapi import APIRouter, HTTPException, Request, Depends, Body
from db_connect import engine as db
from models import Vendas, Clientes, Produtos, ItemVenda
from crud.pagination import PaginationParams
from typing import List, Optional
from bson import ObjectId
from http import HTTPStatus

def router_vendas():
    router = APIRouter(prefix='/vendas', tags=['vendas'])

    @router.get('/', response_model=List[Vendas], description="Lista todas as vendas")
    async def listar_vendas():
        vendas = await db.find(Vendas)
        return vendas

    @router.get('/pagination', response_model=dict, description="Lista todas as vendas com paginação")
    async def get_all_vendas_pagination(pag: PaginationParams = Depends()):
        result_vendas = await pag.pagination(db, Vendas)
        return {
            'resultado': result_vendas['resultado'],
            'prox_id': result_vendas['prox_id'],
            'tamanho': result_vendas['tamanho_pag'],
            'pagina_atual': result_vendas['pagina_atual'],
            'total_paginas': result_vendas['total_paginas']
        }

    @router.get('/atributos', response_model=List[Vendas], description="Lista vendas com base em atributos específicos")
    async def get_vendas_especifico(
        id: Optional[str] = None,
        id_cliente: Optional[str] = None,
        valor_total: Optional[float] = None,
        cliente_programa_fidelidade: Optional[str] = None
    ):
        filtros = {}
        
        if id is not None:
            filtros['_id'] = ObjectId(id)
        if id_cliente is not None:
            try:
                cliente = await db.find_one(Clientes, Clientes.id == ObjectId(id_cliente))
            except Exception:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Cliente não encontrado')
            filtros['cliente'] = cliente
        if valor_total is not None:
            filtros['valor_total'] = valor_total
        if cliente_programa_fidelidade is not None:
            try:
                cliente = await db.find_one(Clientes, Clientes.programa_fidelidade == cliente_programa_fidelidade)
            except Exception:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Cliente não encontrado')
            filtros['cliente'] = cliente
        
        vendas = await db.find(Vendas, filtros)
        if not vendas:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Nenhuma venda encontrada com os filtros fornecidos')
        
        return vendas

    @router.post('/', response_model=Vendas, description="Adiciona uma nova venda")
    async def post_venda(venda: Vendas = Body(
        ...,
        example={
            "cliente": "60d5ec49f1e7e2a5d4e8b5b1",
            "produtos": [
                {"produto": "60d5ec49f1e7e2a5d4e8b5b2", "quantidade": 2},
                {"produto": "60d5ec49f1e7e2a5d4e8b5b3", "quantidade": 1}
            ],
            "valor_total": 150.0
        }
    )):
        cliente = await db.find_one(Clientes, Clientes.id == ObjectId(venda.cliente))
        if cliente is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Cliente não encontrado')
        
        itens_venda = []
        for item in venda.produtos:
            produto = await db.find_one(Produtos, Produtos.id == ObjectId(item.produto))
            if produto is None:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Produto {item.produto} não encontrado')
            itens_venda.append(ItemVenda(produto=produto, quantidade=item.quantidade))
        
        nova_venda = Vendas(cliente=cliente, produtos=itens_venda, valor_total=venda.valor_total)
        nova_venda.valor_total = nova_venda.calcular_valor_total()
        
        await db.save(nova_venda)
        return nova_venda

    @router.put('/{id_venda}', response_model=Vendas, description="Atualiza uma venda existente")
    async def put_venda(id_venda: str, venda_atualizada: Vendas):
        venda = await db.find_one(Vendas, Vendas.id == ObjectId(id_venda))
        if venda is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Venda não encontrada')
        
        cliente = await db.find_one(Clientes, Clientes.id == ObjectId(venda_atualizada.cliente))
        if cliente is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Cliente não encontrado')
        
        itens_venda = []
        for item in venda_atualizada.produtos:
            produto = await db.find_one(Produtos, Produtos.id == ObjectId(item.produto))
            if produto is None:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Produto {item.produto} não encontrado')
            itens_venda.append(ItemVenda(produto=produto, quantidade=item.quantidade))
        
        venda.cliente = cliente
        venda.produtos = itens_venda
        venda.valor_total = venda.calcular_valor_total()
        
        await db.save(venda)
        return venda

    @router.delete('/{id_venda}', response_model=int, description="Deleta uma venda existente")
    async def delete_venda(id_venda: str):
        deleted_count = await db.delete(Vendas, Vendas.id == ObjectId(id_venda))
        if deleted_count == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Venda não encontrada')
        return deleted_count

    return router