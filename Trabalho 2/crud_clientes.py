from fastapi import Depends, HTTPException, APIRouter
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from db_connect import get_db
from db_models import Clientes
from http import HTTPStatus
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

class ClientePy(BaseModel):
    forma_pagamento: str
    programa_fidelidade: Optional[str] = None
    
def route_clientes(pref: str):
    router = APIRouter(prefix=f'/{pref}', tags=[pref])

    @router.get('/')
    def get_all_clientes(db: Session = Depends(get_db)):
        return db.query(Clientes).order_by(Clientes.ID_Cliente).all()

    @router.get('/{id_cliente}')
    def get_cliente(id_cliente: int, db: Session = Depends(get_db)):
        if not id_cliente:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')    
        
        try:
            query = db.query(Clientes).filter_by(ID_Cliente=id_cliente).first() 
            if query is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
        except HTTPException as e:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f'Erro ao retornar o cliente. Erro: {str(e)}')
        return query

    @router.post('/')
    def create_cliente(cliente_req: ClientePy, db: Session = Depends(get_db)):        
        try:
            cliente = Clientes(
                forma_pagamento=cliente_req.forma_pagamento,
                programa_fidelidade=cliente_req.programa_fidelidade
            )
            db.add(cliente)
            db.commit()
            db.refresh(cliente)
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao criar cliente no banco de dados: {str(e)}")
        else:
            return cliente

    @router.put('/{id_cliente}')
    def update_cliente(id_cliente: int, cliente_req: ClientePy, db: Session = Depends(get_db)):
        if not id_cliente:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')
        
        try:
            cliente_db = db.query(Clientes).filter_by(ID_Cliente=id_cliente).first()
            if cliente_db is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
            
            cliente_antigo = {
                "ID_Cliente": cliente_db.ID_Cliente,
                "forma_pagamento": cliente_db.forma_pagamento,
                "programa_fidelidade": cliente_db.programa_fidelidade
            }
            
            cliente_db.forma_pagamento = cliente_req.forma_pagamento
            cliente_db.programa_fidelidade = cliente_req.programa_fidelidade
                
            db.commit()
            db.refresh(cliente_db)
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao atualizar o cliente no banco de dados: {str(e)}")
        else:
            return cliente_antigo

    @router.delete('/{id_cliente}')
    def delete_cliente(id_cliente: int, db: Session = Depends(get_db)):
        if not id_cliente:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')
        
        try:
            del_cliente = db.query(Clientes).filter_by(ID_Cliente=id_cliente).first()
            if del_cliente is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
            db.delete(del_cliente)
            db.commit()        
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao excluir o cliente no banco de dados: {str(e)}")
        else:
            return del_cliente
    
    return router