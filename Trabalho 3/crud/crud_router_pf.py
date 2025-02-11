from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from db_connect import engine as db
from models import ProdutosFornecidos, Produtos, Fornecedores
from pagination import PaginationParams
from typing import List, Optional
from bson import ObjectId
from http import HTTPStatus

class ProdutosFornecidosPy(BaseModel):
    id: Optional[str] = None
    produto: str # id do produto
    fornecedor: str # id do fornecedor
    quantidade: int
    custo_unidade: float

def router_produtos_fornecidos():
    router = APIRouter(prefix='/produtos-fornecidos', tags=['produtos-fornecidos'])
    
    @router.get('/', response_model=List[ProdutosFornecidosPy])
    async def get_all_produtos_fornecidos():
        produtos_fornecidos = await db.find(ProdutosFornecidos)

        response = [
            ProdutosFornecidosPy(
                id=str(pf.id),
                produto=str(pf.produto.id),
                fornecedor=str(pf.fornecedor.id),
                quantidade=pf.quantidade,
                custo_unidade=pf.custo_unidade
            ) for pf in produtos_fornecidos
        ]
        
        return response
    
    @router.get('/pagination', response_model=List[ProdutosFornecidosPy])
    async def get_all_pf_pagination(pag: PaginationParams):
        ultimo_id = pag.ultimo_id
        if ultimo_id is None:
            ultimo_id = await db.find_one(ProdutosFornecidos, sort=ProdutosFornecidos.id)

        result_pf = await db.find(ProdutosFornecidos, ProdutosFornecidos.id > ObjectId(ultimo_id), limit=pag.tamanho)

        return [
            ProdutosFornecidosPy(
                id=str(pf.id),
                produto=pf.produto,
                fornecedor=pf.fornecedor,
                quantidade=pf.quantidade,
                custo_unidade=pf.custo_unidade
            ) for pf in result_pf
        ]
        
    @router.get('/atributos', response_model=List[ProdutosFornecidosPy])
    async def get_produtos_fornecidos_especifico(req: Request):
        atributos = req.query_params
            
        filtros = {}
        
        for chave, valor in atributos.items():
            if chave in ProdutosFornecidos.model_fields:
                tipo_chave = ProdutosFornecidos.model_fields[chave].annotation
                try:
                    valor_convertido = tipo_chave(valor)
                except (ValueError, TypeError):
                    raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f"Valor inválido para o atributo {chave}. Esperado: {tipo_chave}"
                    )
                
                filtros[chave] = valor_convertido
        
        produtos_fornecidos = await db.find(ProdutosFornecidos, filtros)
        
        if not produtos_fornecidos:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Nenhum produto fornecido encontrado com os filtros fornecidos')
        
        return [
            ProdutosFornecidosPy(
                id=str(pf.id),
                produto=str(pf.produto.id),
                fornecedor=str(pf.fornecedor.id),
                quantidade=pf.quantidade,
                custo_unidade=pf.custo_unidade
            ) for pf in produtos_fornecidos
        ]
        
    @router.post('/', response_model=ProdutosFornecidosPy)
    async def post_produto_fornecido(pf: ProdutosFornecidosPy):
        produto = await db.find_one(Produtos, Produtos.id == ObjectId(pf.produto))
        if produto is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto não encontrado')
        
        fornecedor = await db.find_one(Fornecedores, Fornecedores.id == ObjectId(pf.fornecedor))
        if fornecedor is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Fornecedor não encontrado')
        
        try:
            novo_pf = ProdutosFornecidos(
                produto=produto,
                fornecedor=fornecedor,
                quantidade=pf.quantidade,
                custo_unidade=pf.custo_unidade
            )
        except Exception as e:
            HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f'Erro ao criar produto fornecido. Erro: {str(e)}')
        
        await db.save(novo_pf)
        
        return ProdutosFornecidosPy(
            id=str(novo_pf.id),
            produto=str(novo_pf.produto.id),
            fornecedor=str(novo_pf.fornecedor.id),
            quantidade=novo_pf.quantidade,
            custo_unidade=novo_pf.custo_unidade
        )

    @router.put('/{id_pf}', response_model=ProdutosFornecidosPy)
    async def put_produto_fornecido(id_pf: str, pf_atualizado: ProdutosFornecidosPy):
        pf = await db.find_one(ProdutosFornecidos, ProdutosFornecidos.id == ObjectId(id_pf))
        if pf is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto fornecido não encontrado')
        
        produto = await db.find_one(Produtos, Produtos.id == ObjectId(pf_atualizado.produto))
        if produto is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto não encontrado')
        
        fornecedor = await db.find_one(Fornecedores, Fornecedores.id == ObjectId(pf_atualizado.fornecedor))
        if fornecedor is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Fornecedor não encontrado')
        
        pf.produto = produto
        pf.fornecedor = fornecedor
        pf.quantidade = pf_atualizado.quantidade
        pf.custo_unidade = pf_atualizado.custo_unidade
        
        await db.save(pf)
        
        return ProdutosFornecidosPy(
            id=str(pf.id),
            produto=str(pf.produto.id),
            fornecedor=str(pf.fornecedor.id),
            quantidade=pf.quantidade,
            custo_unidade=pf.custo_unidade
        )

    @router.delete('/{id_pf}', response_model=int)
    async def delete_produto_fornecido(id_pf: str):

        deleted_count = await db.delete(ProdutosFornecidos, ProdutosFornecidos.id == ObjectId(id_pf))
        
        if deleted_count == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto fornecido não encontrado')
        
        return deleted_count

    return router
