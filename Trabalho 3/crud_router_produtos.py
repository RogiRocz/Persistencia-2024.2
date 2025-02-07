from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db_connect import engine as db
from models import Produtos
from typing import List, Optional
from pagination import PaginationParams
from bson import ObjectId
from http import HTTPStatus

class ProdutoPy(BaseModel):
    id: Optional[str] = None
    codigo_barras: str
    nome: str
    valor_unitario: float

def router_produtos():
    router = APIRouter(prefix='/produtos', tags=['produtos'])

    @router.get('/', response_model=List[ProdutoPy])
    async def get_all_produtos():
        produtos = await db.find(Produtos)
        
        response = [
            ProdutoPy(
                id=str(produto.id),
                nome=produto.nome,
                codigo_barras=produto.codigo_barras,
                valor_unitario=produto.valor_unitario
            )
            for produto in produtos
        ]
        
        return response
    
    @router.get('/pagination', response_model=List[ProdutoPy])
    async def get_all_produtos_pagination(pag: PaginationParams):
        ultimo_id = pag.ultimo_id
        if ultimo_id is None:
            ultimo_id = await db.find_one(Produtos, sort=Produtos.id)
        
        result_produtos = await db.find(Produtos, Produtos.id > ObjectId(ultimo_id), limit=pag.tamanho)
        
        return [ProdutoPy(
            id=str(produto.id),
            nome=produto.nome,
            codigo_barras=produto.codigo_barras,
            valor_unitario=produto.valor_unitario
        ) for produto in result_produtos]
        

    @router.post('/', response_model=ProdutoPy)
    async def post_produto(produto: ProdutoPy):
        novo_produto = Produtos(
            nome=produto.nome,
            codigo_barras=produto.codigo_barras,
            valor_unitario=produto.valor_unitario
        )
        
        await db.save(novo_produto)
        
        return ProdutoPy(
            id=str(novo_produto.id),
            nome=novo_produto.nome,
            codigo_barras=novo_produto.codigo_barras,
            valor_unitario=novo_produto.valor_unitario
        )
        
    @router.put('/{id_produto}', response_model=ProdutoPy)
    async def put_produto(id_produto:str, novo_produto: ProdutoPy):
        antigo_produto = await db.find_one(Produtos, Produtos.id == ObjectId(id_produto))
        if antigo_produto is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND ,detail=f'Produto não encontrado')
        
        antigo_produto.nome = novo_produto.nome
        antigo_produto.codigo_barras = novo_produto.codigo_barras
        antigo_produto.valor_unitario = novo_produto.valor_unitario
                
        await db.save(antigo_produto)
        
        return ProdutoPy(
            id=str(antigo_produto.id),
            nome=antigo_produto.nome,
            codigo_barras=antigo_produto.codigo_barras,
            valor_unitario=antigo_produto.valor_unitario
        )
    
    @router.delete('/{id_produto}', response_model=int)
    async def delete_produto(id_produto: str):
        deleted_count = await db.remove(Produtos, Produtos.id == ObjectId(id_produto), just_one=True)
        
        if deleted_count == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Produto não encontrado')
        
        return deleted_count
        
    return router