from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db_connect import engine as db
from models import Fornecedores
from pagination import PaginationParams
from typing import List, Optional
from bson import ObjectId
from http import HTTPStatus

class FornecedoresPy(BaseModel):
    id = Optional[str] = None
    nome = str
    cnpj = str
    endereco = str
    
def router_fornecedores():
    router = APIRouter(prefix='/fornecedores', tags=['fornecedores'])
    
    @router.get('/', response_model=List[FornecedoresPy])
    async def get_all_fornecedores():
        fornecedores = await db.find(Fornecedores)
        
        return [
            FornecedoresPy(
                id=str(fornecedor.id),
                nome=fornecedor.nome,
                cnpj=fornecedor.cnpj,
                endereco=fornecedor.endereco
            )for fornecedor in fornecedores
        ]
    
    @router.get('/pagination', response_model=List[FornecedoresPy])
    async def get_all_fornecedores_pagination(pag: PaginationParams):
        ultimo_id = pag.ultimo_id
        if ultimo_id is None:
            ultimo_id = await db.find_one(Fornecedores, sort=Fornecedores.id)
            
        result_fornecedores = await db.find(Fornecedores, Fornecedores.id > ObjectId(ultimo_id), limit=pag.tamanho)

        return [
            FornecedoresPy(
                id=str(fornecedor.id),
                nome=fornecedor.nome,
                cnpj=fornecedor.cnpj,
                endereco=fornecedor.endereco
            ) for fornecedor in result_fornecedores
        ]
        
    @router.post('/', response_model=FornecedoresPy)
    async def post_fornecedor(fornecedor: FornecedoresPy):
        try:
            novo_fornecedor = Fornecedores(
                nome=fornecedor.nome,
                cnpj=fornecedor.cnpj,
                endereco=fornecedor.endereco    
            )
        except Exception as e:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f'Erro a criar fornecedor. Erro: {str(e)}')
        else:
            await db.save(novo_fornecedor)
            
            return FornecedoresPy(
                id=str(novo_fornecedor.id),
                nome=novo_fornecedor.nome,
                cnpj=novo_fornecedor.cnpj,
                endereco=novo_fornecedor.endereco
            )
            
    @router.put('/{id_fornecedor}', response_model=FornecedoresPy)
    async def put_fornecedor(id_fornecedor: str, novo_fornecedor: FornecedoresPy):
        antigo_fornecedor = await db.find_one(Fornecedores, Fornecedores.id == ObjectId(id_fornecedor))
        if antigo_fornecedor is None:
            raise HTTPException(status_code=HTTPStatus, detail=f'Fornecedor não encontrado')
        
        antigo_fornecedor.nome = novo_fornecedor.nome
        antigo_fornecedor.cnpj = novo_fornecedor.cnpj
        antigo_fornecedor.endereco = novo_fornecedor.endereco
        
        await db.save(antigo_fornecedor)
        
        return FornecedoresPy(
            id=str(antigo_fornecedor.id),
            nome=antigo_fornecedor.nome,
            cnpj=antigo_fornecedor.cnpj,
            endereco=antigo_fornecedor.endereco
        )
        
    @router.delete('/{id_fornecedor}', response_model=int)
    async def delete_fornecedor(id_fornecedor: str):
        deleted_count = await db.remove(Fornecedores, Fornecedores.id == ObjectId(id_fornecedor), just_one=True)
        
        if deleted_count == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Fornecedor não encontrado')
        
        return deleted_count
    
    
    return router
