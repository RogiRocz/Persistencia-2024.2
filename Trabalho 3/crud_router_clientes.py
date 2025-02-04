from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db_connect import engine as db
from models import Clientes
from typing import List, Optional
from bson import ObjectId
from http import HTTPStatus

class ClientesPy(BaseModel):
    id: Optional[str] = None
    forma_pagamento: str
    programa_fidelidade: Optional[str]

def router_clientes():
    router = APIRouter(prefix='/clientes', tags=['clientes'])
    
    @router.get('/', response_model=List[ClientesPy])
    async def get_all_clientes():
        clientes = await db.find(Clientes)
        
        response = [
            ClientesPy(
                id=str(cliente.id),
                forma_pagamento=cliente.forma_pagamento,
                programa_fidelidade=cliente.programa_fidelidade
            ) for cliente in clientes
        ]
        
        return response
        
    @router.post('/', response_model=ClientesPy)
    async def post_cliente(cliente: ClientesPy):
        novo_cliente = Clientes(
            forma_pagamento=cliente.forma_pagamento, 
            programa_fidelidade=cliente.programa_fidelidade
        )
        
        await db.save(novo_cliente) 

        return ClientesPy(
            id=str(novo_cliente.id),
            forma_pagamento=novo_cliente.forma_pagamento,
            programa_fidelidade=novo_cliente.programa_fidelidade
        )

    @router.put('/{id_cliente}', response_model=ClientesPy)
    async def put_cliente(id_cliente: str, cliente_atualizado: ClientesPy):
        cliente = await db.find_one(Clientes, Clientes.id == ObjectId(id_cliente))
        if cliente is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Cliente não encontrado')

        cliente.forma_pagamento = cliente_atualizado.forma_pagamento
        cliente.programa_fidelidade = cliente_atualizado.programa_fidelidade
        
        await db.save(cliente)

        return ClientesPy(
            id=str(cliente.id),
            forma_pagamento=cliente.forma_pagamento,
            programa_fidelidade=cliente.programa_fidelidade
        )

    @router.delete('/{id_cliente}', response_model=int)
    async def delete_cliente(id_cliente: str):
        deleted_count = await db.delete(Clientes, Clientes.id == ObjectId(id_cliente))
        
        if deleted_count == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Cliente não encontrado')
        
        return deleted_count

    return router