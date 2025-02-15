from fastapi import APIRouter, Depends, HTTPException, Request
from db_connect import engine as db
from models import Fornecedores
from crud.pagination import PaginationParams
from typing import List, Optional
from bson import ObjectId
from http import HTTPStatus

def router_fornecedores():
    router = APIRouter(prefix='/fornecedores', tags=['fornecedores'])
    
    @router.get('/', response_model=List[Fornecedores], description="Lista todos os fornecedores")
    async def get_all_fornecedores():
        fornecedores = await db.find(Fornecedores)
        return fornecedores
    
    @router.get('/pagination', response_model=dict, description="Lista todos os fornecedores com paginação")
    async def get_all_fornecedores_pagination(pag: PaginationParams = Depends()):
        result_fornecedores = await pag.pagination(db, Fornecedores)
        return {
            'resultado': result_fornecedores['resultado'],
            'prox_id': result_fornecedores['prox_id'],
            'tamanho': result_fornecedores['tamanho_pag'],
            'pagina_atual': result_fornecedores['pagina_atual'],
            'total_paginas': result_fornecedores['total_paginas']
        }
        
    @router.get('/atributos', response_model=List[Fornecedores], description="Lista fornecedores específicos com base em atributos")
    async def get_fornecedores_especificos(
        id: Optional[str] = None,
        nome: Optional[str] = None,
        cnpj: Optional[str] = None
    ):
        filtros = {}
        
        if id is not None:
            filtros['_id'] = ObjectId(id)
        if nome is not None:
            filtros['nome'] = {"$regex": f".*{nome}.*", "$options": "i"}
        if cnpj is not None:
            filtros['cnpj'] = cnpj
        
        fornecedores = await db.find(Fornecedores, filtros)
        if not fornecedores:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Nenhum fornecedor encontrado com os filtros fornecidos')
                
        return fornecedores
        
    @router.post('/', response_model=Fornecedores, description="Adiciona um novo fornecedor")
    async def post_fornecedor(fornecedor: Fornecedores):
        await db.save(fornecedor)
        return fornecedor
            
    @router.put('/{id_fornecedor}', response_model=Fornecedores, description="Atualiza um fornecedor existente")
    async def put_fornecedor(id_fornecedor: str, novo_fornecedor: Fornecedores):
        antigo_fornecedor = await db.find_one(Fornecedores, Fornecedores.id == ObjectId(id_fornecedor))
        if antigo_fornecedor is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Fornecedor não encontrado')
        
        antigo_fornecedor.nome = novo_fornecedor.nome if novo_fornecedor.nome else antigo_fornecedor.nome
        antigo_fornecedor.cnpj = novo_fornecedor.cnpj if novo_fornecedor.cnpj else antigo_fornecedor.cnpj
        antigo_fornecedor.endereco = novo_fornecedor.endereco if novo_fornecedor.endereco else antigo_fornecedor.endereco
        
        await db.save(antigo_fornecedor)
        return antigo_fornecedor
        
    @router.delete('/{id_fornecedor}', response_model=int, description="Deleta um fornecedor existente")
    async def delete_fornecedor(id_fornecedor: str):
        deleted_count = await db.remove(Fornecedores, Fornecedores.id == ObjectId(id_fornecedor), just_one=True)
        if deleted_count == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Fornecedor não encontrado')
        return deleted_count
    
    return router
