from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db_connect import engine as db
from models import Vendas, Clientes, Produtos, ItemVenda
from pagination import PaginationParams
from typing import List, Optional
from bson import ObjectId
from http import HTTPStatus

class ItemVendaPy(BaseModel):
    produto: str  # ID do produto
    quantidade: int

class VendasPy(BaseModel):
    id: Optional[str] = None  # O ID é opcional e será gerado pelo MongoDB
    cliente: str  # ID do cliente
    produtos: List[ItemVendaPy]
    valor_total: float

def router_vendas():
    router = APIRouter(prefix='/vendas', tags=['vendas'])
    
    @router.get('/', response_model=List[VendasPy])
    async def get_all_vendas():
        vendas = await db.find(Vendas)
        
        response = [
            VendasPy(
                id=str(venda.id),
                cliente=str(venda.cliente.id),
                produtos=[
                    ItemVendaPy(
                        produto=str(item.produto.id),
                        quantidade=item.quantidade
                    ) for item in venda.produtos
                ],
                valor_total=venda.valor_total
            ) for venda in vendas
        ]
        
        return response
    
    @router.get('/pagination', response_model=List[VendasPy])
    async def get_all_vendas_pagination(pag: PaginationParams):
        ultimo_id = pag.ultimo_id
        if ultimo_id is None:
            ultimo_id = await db.find_one(Vendas, sort=Vendas.id)
            
        result_vendas = await db.find(Vendas, Vendas.id > ObjectId(ultimo_id), limit=pag.tamanho)
        
        return [
            VendasPy(
                id=str(venda.id),
                cliente=venda.cliente,
                produtos=venda.produtos,
                valor_total=venda.valor_total
            ) for venda in result_vendas
        ]
    
    @router.post('/', response_model=VendasPy)
    async def post_venda(venda: VendasPy):
        cliente = await db.find_one(Clientes, Clientes.id == ObjectId(venda.cliente))
        if cliente is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Cliente não encontrado')
        
        itens_venda = []
        for item in venda.produtos:
            produto = await db.find_one(Produtos, Produtos.id == ObjectId(item.produto))
            if produto is None:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Produto {item.produto} não encontrado')
            
            itens_venda.append(ItemVenda(produto=produto, quantidade=item.quantidade))
        
        nova_venda = Vendas(
            cliente=cliente,
            produtos=itens_venda,
            valor_total=venda.valor_total
        )
        
        nova_venda.valor_total = nova_venda.calcular_valor_total()
        
        await db.save(nova_venda)
        
        return VendasPy(
            id=str(nova_venda.id),
            cliente=str(nova_venda.cliente.id),
            produtos=[
                ItemVendaPy(
                    produto=str(item.produto.id),
                    quantidade=item.quantidade
                ) for item in nova_venda.produtos
            ],
            valor_total=nova_venda.valor_total
        )

    @router.put('/{id_venda}', response_model=VendasPy)
    async def put_venda(id_venda: str, venda_atualizada: VendasPy):
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
        venda.valor_total = venda_atualizada.valor_total
        
        venda.valor_total = venda.calcular_valor_total()
        
        await db.save(venda)
        
        return VendasPy(
            id=str(venda.id),
            cliente=str(venda.cliente.id),
            produtos=[
                ItemVendaPy(
                    produto=str(item.produto.id),
                    quantidade=item.quantidade
                ) for item in venda.produtos
            ],
            valor_total=venda.valor_total
        )

    @router.delete('/{id_venda}', response_model=int)
    async def delete_venda(id_venda: str):
        deleted_count = await db.delete(Vendas, Vendas.id == ObjectId(id_venda))
        
        if deleted_count == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Venda não encontrada')
        
        return deleted_count

    return router