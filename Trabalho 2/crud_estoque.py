from fastapi import Depends, HTTPException, APIRouter
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from db_connect import get_db
from db_models import Estoque
from http import HTTPStatus
from sqlalchemy.exc import SQLAlchemyError

class EstoquePy(BaseModel):
    ID_Fornecedor: int
    ID_Produto: int
    quantidade: int
    categoria: str = None
    validade_dias: int

def route_estoque(pref: str):
    router = APIRouter(prefix=f'/{pref}', tags=[pref])

    @router.get('/')
    def get_all_estoque(db: Session = Depends(get_db)):
        return db.query(Estoque).order_by(Estoque.ID_Estoque).all()

    @router.get('/{id_estoque}')
    def get_estoque(id_estoque: int, db: Session = Depends(get_db)):
        if not id_estoque:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')    
        
        try:
            query = db.query(Estoque).filter_by(ID_Estoque=id_estoque).first() 
            if query is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
        except HTTPException as e:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f'Erro ao retornar o estoque. Erro: {str(e)}')
        return query

    @router.post('/')
    def create_estoque(estoque_req: EstoquePy, db: Session = Depends(get_db)):
        if not estoque_req.ID_Fornecedor or not estoque_req.ID_Produto:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="ID do fornecedor e do produto são obrigatórios.")
        if estoque_req.quantidade <= 0:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="A quantidade deve ser maior que zero.")
        if estoque_req.validade_dias <= 0:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="A validade em dias deve ser maior que zero.")
        
        try:
            estoque = Estoque(
                ID_Fornecedor=estoque_req.ID_Fornecedor,
                ID_Produto=estoque_req.ID_Produto,
                quantidade=estoque_req.quantidade,
                categoria=estoque_req.categoria,
                validade_dias=estoque_req.validade_dias
            )
            db.add(estoque)
            db.commit()
            db.refresh(estoque)
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao criar estoque no banco de dados: {str(e)}")
        else:
            return estoque

    @router.put('/{id_estoque}')
    def update_estoque(id_estoque: int, estoque_req: EstoquePy, db: Session = Depends(get_db)):
        if not id_estoque:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')
        
        try:
            estoque_db = db.query(Estoque).filter_by(ID_Estoque=id_estoque).first()
            if estoque_db is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
            
            estoque_antigo = {
                "ID_Estoque": estoque_db.ID_Estoque,
                "ID_Fornecedor": estoque_db.ID_Fornecedor,
                "ID_Produto": estoque_db.ID_Produto,
                "quantidade": estoque_db.quantidade,
                "categoria": estoque_db.categoria,
                "validade_dias": estoque_db.validade_dias
            }
            
            estoque_db.ID_Fornecedor = estoque_req.ID_Fornecedor
            estoque_db.ID_Produto = estoque_req.ID_Produto
            estoque_db.quantidade = estoque_req.quantidade
            estoque_db.categoria = estoque_req.categoria
            estoque_db.validade_dias = estoque_req.validade_dias
                
            db.commit()
            db.refresh(estoque_db)
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao atualizar o estoque no banco de dados: {str(e)}")
        else:
            return estoque_antigo

    @router.delete('/{id_estoque}')
    def delete_estoque(id_estoque: int, db: Session = Depends(get_db)):
        if not id_estoque:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')
        
        try:
            del_estoque = db.query(Estoque).filter_by(ID_Estoque=id_estoque).first()
            if del_estoque is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
            db.delete(del_estoque)
            db.commit()        
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao excluir o estoque no banco de dados: {str(e)}")
        else:
            return del_estoque
    
    return router