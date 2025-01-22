from fastapi import Depends, HTTPException, APIRouter
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from db_connect import get_db
from db_models import Fornecedores
from http import HTTPStatus
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal


class FornecedorPy(BaseModel):
    nome: str
    ID_Produto: int
    quantidade: int
    valor_unitario: Decimal = Field(max_digits=10, decimal_places=2)
    
    @validator('valor_unitario')
    def validate_valor_unitario(cls, value):
        value_str = str(value)
        if len(value_str.replace('.', '')) > 10:
            raise ValueError('O valor unitário não pode ter mais de 10 dígitos no total.')
        if '.' in value_str and len(value_str.split('.')[1]) > 2:
            raise ValueError('O valor unitário não pode ter mais de 2 casas decimais.')
        return value
    
def route_fornecedores(pref: str):
    router = APIRouter(prefix=f'/{pref}', tags=[pref])

    @router.get('/')
    def get_all_fornecedores(db: Session = Depends(get_db)):
        return db.query(Fornecedores).order_by(Fornecedores.ID_Fornecedor).all()

    @router.get('/{id_fornecedor}')
    def get_fornecedor(id_fornecedor: int, db: Session = Depends(get_db)):
        if not id_fornecedor:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')    
        
        try:
            query = db.query(Fornecedores).filter_by(ID_Fornecedor=id_fornecedor).first() 
            if query is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
        except HTTPException as e:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f'Erro ao retornar o fornecedor. Erro: {str(e)}')
        return query

    @router.post('/')
    def create_fornecedor(fornecedor_req: FornecedorPy, db: Session = Depends(get_db)):
        if not fornecedor_req.nome:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="O nome do fornecedor não pode estar vazio.")
        if fornecedor_req.quantidade <= 0:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="A quantidade deve ser maior que zero.")
        if fornecedor_req.valor_unitario <= 0:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="O valor unitário deve ser maior que zero.")
        
        try:
            fornecedor = Fornecedores(
                nome=fornecedor_req.nome,
                ID_Produto=fornecedor_req.ID_Produto,
                quantidade=fornecedor_req.quantidade,
                valor_unitario=fornecedor_req.valor_unitario
            )
            db.add(fornecedor)
            db.commit()
            db.refresh(fornecedor)
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao criar fornecedor no banco de dados: {str(e)}")
        else:
            return fornecedor

    @router.put('/{id_fornecedor}')
    def update_fornecedor(id_fornecedor: int, fornecedor_req: FornecedorPy, db: Session = Depends(get_db)):
        if not id_fornecedor:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')
        
        try:
            fornecedor_db = db.query(Fornecedores).filter_by(ID_Fornecedor=id_fornecedor).first()
            if fornecedor_db is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
            
            fornecedor_antigo = {
                "ID_Fornecedor": fornecedor_db.ID_Fornecedor,
                "nome": fornecedor_db.nome,
                "ID_Produto": fornecedor_db.ID_Produto,
                "quantidade": fornecedor_db.quantidade,
                "valor_unitario": fornecedor_db.valor_unitario
            }
            
            fornecedor_db.nome = fornecedor_req.nome
            fornecedor_db.ID_Produto = fornecedor_req.ID_Produto
            fornecedor_db.quantidade = fornecedor_req.quantidade
            fornecedor_db.valor_unitario = fornecedor_req.valor_unitario
                
            db.commit()
            db.refresh(fornecedor_db)
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao atualizar o fornecedor no banco de dados: {str(e)}")
        else:
            return fornecedor_antigo

    @router.delete('/{id_fornecedor}')
    def delete_fornecedor(id_fornecedor: int, db: Session = Depends(get_db)):
        if not id_fornecedor:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')
        
        try:
            del_fornecedor = db.query(Fornecedores).filter_by(ID_Fornecedor=id_fornecedor).first()
            if del_fornecedor is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
            db.delete(del_fornecedor)
            db.commit()        
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao excluir o fornecedor no banco de dados: {str(e)}")
        else:
            return del_fornecedor
    
    return router