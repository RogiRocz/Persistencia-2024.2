from fastapi import Depends, HTTPException, APIRouter
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from db_connect import get_db
from db_models import Vendas
from http import HTTPStatus
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal

class VendaPy(BaseModel):
    ID_Cliente: int
    ID_Produto: int
    quantidade: int
    valor_total: Decimal = Field(max_digits=10, decimal_places=2)
    
    @validator('valor_unitario')
    def validate_valor_total(cls, value):
        value_str = str(value)
        if len(value_str.replace('.', '')) > 10:
            raise ValueError('O valor unitário não pode ter mais de 10 dígitos no total.')
        if '.' in value_str and len(value_str.split('.')[1]) > 2:
            raise ValueError('O valor unitário não pode ter mais de 2 casas decimais.')
        return value

def route_vendas(pref: str):
    router = APIRouter(prefix=f'/{pref}', tags=[pref])

    @router.get('/')
    def get_all_vendas(db: Session = Depends(get_db)):
        return db.query(Vendas).order_by(Vendas.ID_Venda).all()

    @router.get('/{id_venda}')
    def get_venda(id_venda: int, db: Session = Depends(get_db)):
        if not id_venda:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')    
        
        try:
            query = db.query(Vendas).filter_by(ID_Venda=id_venda).first() 
            if query is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
        except HTTPException as e:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f'Erro ao retornar a venda. Erro: {str(e)}')
        return query

    @router.post('/')
    def create_venda(venda_req: VendaPy, db: Session = Depends(get_db)):
        if not venda_req.ID_Cliente or not venda_req.ID_Produto:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="ID do cliente e do produto são obrigatórios.")
        
        try:
            venda = Vendas(
                ID_Cliente=venda_req.ID_Cliente,
                ID_Produto=venda_req.ID_Produto,
                quantidade=venda_req.quantidade,
                valor_total=venda_req.valor_total
            )
            db.add(venda)
            db.commit()
            db.refresh(venda)
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao criar venda no banco de dados: {str(e)}")
        else:
            return venda

    @router.put('/{id_venda}')
    def update_venda(id_venda: int, venda_req: VendaPy, db: Session = Depends(get_db)):
        if not id_venda:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')
        
        try:
            venda_db = db.query(Vendas).filter_by(ID_Venda=id_venda).first()
            if venda_db is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
            
            venda_antigo = {
                "ID_Venda": venda_db.ID_Venda,
                "ID_Cliente": venda_db.ID_Cliente,
                "ID_Produto": venda_db.ID_Produto,
                "quantidade": venda_db.quantidade,
                "valor_total": venda_db.valor_total
            }
            
            venda_db.ID_Cliente = venda_req.ID_Cliente
            venda_db.ID_Produto = venda_req.ID_Produto
            venda_db.quantidade = venda_req.quantidade
            venda_db.valor_total = venda_req.valor_total
                
            db.commit()
            db.refresh(venda_db)
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao atualizar a venda no banco de dados: {str(e)}")
        else:
            return venda_antigo

    @router.delete('/{id_venda}')
    def delete_venda(id_venda: int, db: Session = Depends(get_db)):
        if not id_venda:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')
        
        try:
            del_venda = db.query(Vendas).filter_by(ID_Venda=id_venda).first()
            if del_venda is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
            db.delete(del_venda)
            db.commit()        
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao excluir a venda no banco de dados: {str(e)}")
        else:
            return del_venda
    
    return router