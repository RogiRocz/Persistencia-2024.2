from fastapi import APIRouter, Depends, HTTPException, Request
from db_connect import engine as db
from models import Clientes
from crud.pagination import PaginationParams
from typing import List, Optional
from bson import ObjectId
from http import HTTPStatus

def router_clientes():
    router = APIRouter(prefix='/clientes', tags=['clientes'])

    @router.get('/', response_model=List[Clientes], description="Lista todos os clientes")
    async def listar_clientes():
        clientes = await db.find(Clientes)
        return clientes

    @router.get('/pagination', response_model=dict, description="Lista todos os clientes com paginação")
    async def get_all_clientes_pagination(pag: PaginationParams = Depends()):
        result_clientes = await pag.pagination(db, Clientes)
        return {
            'resultado': result_clientes['resultado'],
            'prox_id': result_clientes['prox_id'],
            'tamanho': result_clientes['tamanho_pag'],
            'pagina_atual': result_clientes['pagina_atual'],
            'total_paginas': result_clientes['total_paginas']
        }
        
    @router.get('/atributos', response_model=List[Clientes], description="Obtém clientes específicos com base em atributos")
    async def get_clientes_especificos(
        id: Optional[str] = None,
        forma_pagamento: Optional[str] = None,
        programa_fidelidade: Optional[str] = None
    ):
        filtros = {}
        
        if id is not None:
            filtros['_id'] = ObjectId(id)
        if forma_pagamento is not None:
            filtros['forma_pagamento'] = forma_pagamento
        if programa_fidelidade is not None:
            filtros['programa_fidelidade'] = programa_fidelidade
        
        clientes = await db.find(Clientes, filtros)
        if not clientes:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Nenhum cliente encontrado com os filtros fornecidos')
                
        return clientes
    
    @router.post('/', response_model=Clientes, description="Adiciona um novo cliente")
    async def post_cliente(cliente: Clientes):
        await db.save(cliente)
        return cliente

    @router.put('/{id_cliente}', response_model=Clientes, description="Atualiza um cliente existente")
    async def put_cliente(id_cliente: str, cliente_atualizado: Clientes):
        cliente = await db.find_one(Clientes, Clientes.id == ObjectId(id_cliente))
        if cliente is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Cliente não encontrado')

        cliente.forma_pagamento = cliente_atualizado.forma_pagamento if cliente_atualizado.forma_pagamento else cliente.forma_pagamento
        cliente.programa_fidelidade = cliente_atualizado.programa_fidelidade if cliente_atualizado.programa_fidelidade else cliente.programa_fidelidade
        
        await db.save(cliente)
        return cliente

    @router.delete('/{id_cliente}', response_model=int, description="Deleta um cliente existente")
    async def delete_cliente(id_cliente: str):
        deleted_count = await db.delete(Clientes, Clientes.id == ObjectId(id_cliente))
        if deleted_count == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Cliente não encontrado')
        return deleted_count

    return router